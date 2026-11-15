"""Host-owned three-source capture for existing presence projection. No connector/server."""
import copy
from dataclasses import dataclass,asdict
from datetime import datetime
from typing import Callable,Optional,TypedDict
from . import agent_presence as presence
from .delegation import sha,encode,HEX
from .resource_admission import resources


@dataclass(frozen=True)
class Source:
    ref: str
    read: Callable[[],object]
    attest: Callable[[object,presence.Selection],bool]


class Capture(TypedDict):
    schema: str
    state: str
    cause: str
    authority: str
    ownerReply: bool
    selection_ref: Optional[str]
    source_refs: list
    snapshot_ref: Optional[str]
    projection_state: str
    unknowns: list
    capture_ref: str


class PresenceSources:
    """Configure from trusted host only, never model paths/callbacks or JSON grants.

    Providers return original immutable capture data: CLI list[Declaration], journal
    Observation (including ORIGINAL context binding), current Mesa Claim. Their read
    capabilities must not share a declaration-derived source. Distinct refs/functions
    are necessary, not proof: independent must witness physical provenance/fences.
    attest must be live/revocable and must NOT mean only hash or field agreement.
    Reads and host witnesses are bounded and read-only by contract. No retries occur.
    """
    def __init__(self,selection,cli:Source,journal:Source,mesa:Source,*,independent,
                 allow_publication,verify_capability,now:Callable[[],datetime]):
        if (not presence._selection(selection)
                or any(type(s) is not Source for s in (cli,journal,mesa))
                or not all(callable(f) for f in (independent,allow_publication,verify_capability,now))):
            raise ValueError('host_configuration_invalid')
        sources=(cli,journal,mesa)
        if (any(type(s.ref) is not str or not HEX.fullmatch(s.ref)
                or not callable(s.read) or not callable(s.attest) for s in sources)
                or len({s.ref for s in sources})!=3 or len({id(s.read) for s in sources})!=3):
            raise ValueError('three_distinct_sources_required')
        self.selection=selection
        self.sources=sources
        self.independent=independent
        self.allow_publication=allow_publication
        self.verify_capability=verify_capability
        self.now=now

    def capture(self,capabilities=()):
        """Read only the configured sources; a query cannot choose a path or session."""
        snapshot=None
        refs=[s.ref for s in self.sources]
        def finish(cause,ok=False):
            row=dict(schema='agent-presence-capture/1',state='CAPTURED' if ok else 'NO_DATA',
                     cause=cause,authority='none',ownerReply=False,
                     selection_ref=sha(asdict(self.selection)),source_refs=refs,
                     snapshot_ref=snapshot['snapshot_ref'] if ok else None,
                     projection_state=snapshot['state'] if ok else 'NO_DATA',
                     unknowns=['cross_cli_live_presence_E2E','authenticated_agent_source_binding',
                               'exclusive_writer_ownership','real_host_stability','atomic_multi_source_snapshot'])
            row['capture_ref']=sha(row)
            if len(encode(row))>=1024:raise ValueError('capture_bound')
            return {'capture':row,'snapshot':copy.deepcopy(snapshot) if ok else None}
        def read_all():
            values=[]
            for source in self.sources:
                # Detach immediately: a provider changing one shared object later
                # cannot retroactively change the first capture.
                value=copy.deepcopy(source.read())
                if source.attest(copy.deepcopy(value),self.selection) is not True:
                    raise _Rejected('SOURCE_NOT_WITNESSED')
                values.append(value)
            if (type(values[0]) is not list or len(values[0])>32
                    or any(type(d) is not presence.Declaration for d in values[0])
                    or type(values[1]) is not presence.Observation or type(values[2]) is not presence.Claim):
                raise _Rejected('SOURCE_DATA_MISSING_OR_INVALID')
            if values[1].source_ref!=refs[1] or values[2].source_ref!=refs[2]:
                raise _Rejected('SOURCE_IDENTITY_MISMATCH')
            normalized=[[asdict(d) for d in values[0]],asdict(values[1]),asdict(values[2])]
            if len(encode(normalized))>262144:raise _Rejected('SOURCE_BOUND_EXCEEDED')
            return values,sha(normalized)
        try:
            started=self.now()
            resources.age_seconds(started.isoformat(),started)
            if type(capabilities) not in (list,tuple) or len(capabilities)>8:
                return finish('CAPABILITY_BOUND_INVALID')
            if self.independent(self.sources,self.selection) is not True:
                return finish('INDEPENDENT_SOURCE_PROVENANCE_MISSING')
            first,fingerprint=read_all()
            cli,journal,mesa=self.sources
            current=self.now()
            if resources.age_seconds(started.isoformat(),current)>presence.TTL:
                return finish('CAPTURE_DEADLINE_EXCEEDED')
            snapshot=presence.project(self.selection,first[0],first[2],first[1],list(capabilities),now=current,
                allow_publication=self.allow_publication,
                verify_claim=lambda c:mesa.attest(copy.deepcopy(c),self.selection),
                verify_observation=lambda o,d,c:journal.attest(copy.deepcopy(o),self.selection),
                verify_capability=self.verify_capability)
            second,recheck=read_all()
            if fingerprint!=recheck:return finish('SOURCE_CHANGED_DURING_CAPTURE')
            if self.independent(self.sources,self.selection) is not True:
                return finish('INDEPENDENT_SOURCE_PROVENANCE_REVOKED')
            ended=self.now()
            if resources.age_seconds(started.isoformat(),ended)>presence.TTL:
                return finish('CAPTURE_DEADLINE_EXCEEDED')
            # Project at final host time: slow readers cannot preserve freshness.
            snapshot=presence.project(self.selection,second[0],second[2],second[1],list(capabilities),now=ended,
                allow_publication=self.allow_publication,
                verify_claim=lambda c:mesa.attest(copy.deepcopy(c),self.selection),
                verify_observation=lambda o,d,c:journal.attest(copy.deepcopy(o),self.selection),
                verify_capability=self.verify_capability)
            # Witnesses called during projection can revoke/change a source. Final
            # capture detects that change; equality is not an atomicity guarantee.
            final,final_fingerprint=read_all()
            if final_fingerprint!=fingerprint:return finish('SOURCE_CHANGED_DURING_CAPTURE')
            final_now=self.now()
            if resources.age_seconds(started.isoformat(),final_now)>presence.TTL:
                return finish('CAPTURE_DEADLINE_EXCEEDED')
            snapshot=presence.project(self.selection,final[0],final[2],final[1],list(capabilities),now=final_now,
                allow_publication=self.allow_publication,
                verify_claim=lambda c:mesa.attest(copy.deepcopy(c),self.selection),
                verify_observation=lambda o,d,c:journal.attest(copy.deepcopy(o),self.selection),
                verify_capability=self.verify_capability)
            if resources.age_seconds(started.isoformat(),self.now())>presence.TTL:
                return finish('CAPTURE_DEADLINE_EXCEEDED')
            if self.independent(self.sources,self.selection) is not True:
                return finish('INDEPENDENT_SOURCE_PROVENANCE_REVOKED')
            return finish('CONSISTENT_READS_NOT_AUTHENTICATION_OR_AUTHORITY',True)
        except _Rejected as error:
            return finish(str(error))
        except resources.EvidenceTimeError:
            return finish('CAPTURE_CLOCK_INVALID_OR_FUTURE')
        except Exception:
            return finish('SOURCE_UNAVAILABLE_OR_HOST_ERROR')


class _Rejected(ValueError):
    pass
