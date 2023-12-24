{
  description = "Refery flake";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
      in
      {
        packages = {
          refery = mkPoetryApplication { projectDir = self; };
          default = self.packages.${system}.refery;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.refery ];
          packages = [ pkgs.poetry ];
        };
      });
}
