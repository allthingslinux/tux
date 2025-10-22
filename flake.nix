{
  description = "Tux";

  inputs = {
    nixpkgs = {
      type = "github";
      owner = "NixOS";
      repo = "nixpkgs";
      ref = "nixos-unstable";
    };

    flake-parts = {
      type = "github";
      owner = "hercules-ci";
      repo = "flake-parts";
      ref = "main";
    };
  };

  outputs = inputs@{
    self,
    nixpkgs,
    flake-parts,
    ...
  }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "x86_64-darwin"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      perSystem = { pkgs, self', system, ... }: {
        devShells = {
          default = self'.devShells.tux;
          tux = pkgs.callPackage ./shell.nix { inherit pkgs self; };
        };

        apps.envrc = {
          type = "app";
          program = self'.packages.envrc;
        };

        # Creates .envrc if does not exist
        packages.envrc = pkgs.writeShellScriptBin "envrc" ''
          echo

          if [ ! -e ".envrc" ]; then
            echo "Creating .envrc"
            printf "use flake .\n\n\n" | cat - .env.example > .envrc
            echo

            echo "The directory is now set up for direnv usage."
            echo
          else
            echo "Please delete .envrc if you wish to recreate it."
            echo
          fi
        '';
      };
    };
}
