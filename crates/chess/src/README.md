# Chess domain source

The source tree is organized by responsibility:

- `model/` contains foundational, notation-independent chess values;
- `notation/` contains textual formats such as FEN;
- future position, move-generation, and game-state modules remain separate.

Application integration, hardware, and transport concerns do not belong here.
