# Окружение проекта на NixOS: nix-shell, затем python manage.py ...
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (p: [ p.django p.pillow p.docutils ]))
    pkgs.graphviz
    pkgs.sqlite
  ];
}
