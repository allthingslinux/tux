{
  description = "All Thing's Linux discord bot - Tux";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    basePkgs = with pkgs; [
      poetry
      python313

    ];
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [
      ] ++ basePkgs;
      shellHook = ''
        echo "Have fun developing :) - green"
      '';
      pkgs.${system}.default = pkgs.stdenv.mkDerivation {
      };
    };
  };
}