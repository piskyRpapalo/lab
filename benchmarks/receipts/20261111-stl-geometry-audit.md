# 3D STL geometry inspection · 2026-11-11

**State: MEASURED_GEOMETRY_ONLY**. Four existing binary STL mesh files were inspected read-only on the Beelink via SentinelX using Python's standard library. **This is not a text-to-3D, image-to-3D, 3DFabrika model-generation, print, or physical-assembly quality benchmark.**

**Broadcast receipt:** figure=4/4 local STL files with two incidences per undirected mesh edge, zero orientation mismatches, positive signed volume | model=NO_DATA (geometry artifacts, no generative AI model executed) | machine=Beelink-class AMD Ryzen 7 255 workstation | date=2026-11-11 | sha256=NO_DATA (no single four-file aggregate source digest; individual file digests below).

**Benchcard:** machine=Beelink-class AMD Ryzen 7 255 | date=2026-11-11 | runner=Python 3 stdlib binary STL inspection via SentinelX, independent of slicer | quant=IEEE-754 float32 STL coordinates; units unspecified | sha256=NO_DATA (aggregate receipt not archived; individual source hashes below).

## Results

| Synthetic artifact | Bytes | Triangles | Unique vertices | Edges | Non-2-incidence edges | Opposite-directed edge mismatches | Extents (STL coordinate units) | Signed volume (units³) |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| CAD sample A | 14,084 | 280 | 144 | 420 | 0 | 0 | 20 × 18.564 × 3 | +485.4251 |
| CAD sample B | 25,684 | 512 | 256 | 768 | 0 | 0 | 20 × 20 × 3 | +790.4102 |
| CAD sample C | 25,684 | 512 | 256 | 768 | 0 | 0 | 20 × 20 × 3 | +790.4102 |
| CAD sample D | 25,684 | 512 | 256 | 768 | 0 | 0 | 20 × 20 × 3 | +790.4102 |

### Source digests, row order

- Sample A SHA-256: `a20b2055f2c516d1caab76f47b829671ebc4b892db8a79a9d55ffbb3977740f6`.
- Sample B SHA-256: `e2cfcd7ce80ca1cfe153fa91026b4d62e9eac2767fbb5da19bea467443f5c3e8`.
- Sample C SHA-256: `7650a8289c97f2becc4a3e360351c9b041ab8ed7330760298dfe739b57ccba66`.
- Sample D SHA-256: `a8aeb872eef7c77e548de8b82e0d11b9f98ba1ccf4231fd82599fd5a7ddad7b1`.

Digests identify local meshes; they are not cryptographic signatures of an independently attested process. Meshes themselves were not uploaded.

## Method and reproducibility boundary

A read-only Python 3 routine checked for each candidate: the binary STL byte count equals `84 + 50 × triangle_count`; extracted 12 float32 values per triangle (normal and three vertices); counted unique vertex triplets; formed each undirected edge by sorting endpoint tuples; required exactly two triangle incidences per edge; compared directed edge multiplicities to their reversed forms; calculated per-axis max-minus-min extents and signed tetrahedral volume from the triangle vertex coordinates. No dependencies, network upload, model call, slicing, mesh repair, or file modifications were performed. The exact original four STL files remain local; reproduction from this public document alone is **NO_DATA: source mesh bytes not published**. Measurements were collected in one inspection session; an independent rerun is **NO_DATA: not performed**.

STL contains no intrinsic unit declaration; assigning mm or physical tolerances from coordinate magnitudes would be unsupported. The edge tests give evidence of an edge-manifold, consistently oriented triangle shell for these four specific files but cannot establish freedom from self-intersections, printability, functional joint clearance, production tolerances, or the identity/quality of an AI generator.

## 3DFabrika / PEGASON research status

The wider 3DFabrika/PEGASON pipeline for prompt/image to printable, separable parts with assembly instructions is not operationally demonstrated by these meshes. **TRELLIS.2 / Hunyuan3D / image-to-mesh generation: NO_DATA (no measured inference receipt located).** Slicer output, physical print, assembly test and user-level end-to-end: **NO_DATA (not tested)**. Do not merge these geometry checks with the text-model ranking or with [the separate browser colony surface frame benchmark](../colony-surface-20261028/README.md).

For external study, [the public Lab summary issue #164](https://github.com/piskyRpapalo/lab/issues/164) collects this alongside the 2026-11-11 throughput run and the independently measured [24-case text-model matrix](https://github.com/piskyRpapalo/lab/pull/162).

**Agent:** Codex · **Model:** GPT-6 · **Run:** SentinelX Beelink, 2026-11-11.
