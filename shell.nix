{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python313
    poetry
    git
    jq
  ];

  shellHook = ''
    # enters the user's preferred shell using a more robust method
    $(getent passwd $(id -un) | cut -d: -f7 | tr -d '\n')

    # exits after child shell exits
    exit
  '';
}