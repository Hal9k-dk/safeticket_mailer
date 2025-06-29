{ ...
}@args:

{
  imports = [
    ./options.nix
  ];
  options = {};
  config = import ./config.nix args;
}
