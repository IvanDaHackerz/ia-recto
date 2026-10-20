# Recto local website

Start from the IA root with `start-website.ps1` and open the printed URL. The launcher selects free loopback ports and pins the API runtime identity. For dependencies, endpoints, privacy, history, source restrictions and testing see [the application guide](../../../backend/application/README.md).

`npm.cmd test`, `npm.cmd run lint`, and `npm.cmd run build` validate the frontend. `scripts/verify-performance.mjs` reconciles the displayed metrics with the saved backend report. Source/legal review and independent acceptance remain separate from software checks.
