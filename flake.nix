{
  inputs = {
    utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

      in {
        packages.default = pkgs.callPackage ./package.nix {};
      }
    ) // {
      nixosModules.default = ./nixosModule;
      overlays.default = final: prev: {
        safeticket-mailer = final.callPackage ./package.nix {};
      };
    };
}
