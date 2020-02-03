# Houdini-FEBio-Toolkit
_A toolkit creating and runing FEBio jobs from within Houdini_

This repository provides a number of tools for running [FEBio](https://febio.org/) simulations from the Houdini interface. This provides a more user friendly experience for interacting with the powerful FEBio simulation software.

> **NOTE:** The demo files included makes use of our [extet](https://github.com/pd3d/extet) bridge for Houdini and TetGen. The demo file: `FEBio_Example.hipnc` will run without the library installed, but will fail if you unfreeze the Null node containing the tetmesh, however, the file `MultiMaterials_Example.hipnc` may become unstable if opened without having an installed version of TetGen.
