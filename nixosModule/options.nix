{ lib
, pkgs
, ...
}: let

  username = "safeticket-mailer";

  inherit (lib)
    mkEnableOption
    mkPackageOption
    mkOption
    literalExpression
  ;

  inherit (lib.types)
    str
    path
    package
    either
    listOf
  ;

in
{
  imports = [];

  options = {
    services.safeticket-mailer = {
      enable = mkEnableOption "Safeticket Mailer";

      sendEmails = mkEnableOption ''
        the sending of emails.
        Should be enabled when you are done testing
        if Safeticket Mailer is configured correctly.
      '';

      package = mkOption {
        type = package;
        default = pkgs.safeticket-mailer;
        defaultText = literalExpression "pkgs.safeticket-mailer";
        description = "The safeticket-mailer package to use.";
      };

      user = mkOption {
        type = str;
        default = "safeticket-mailer";
        description = "User under which Safeticket Mailer runs.";
      };

      group = mkOption {
        type = str;
        default = "safeticket-mailer";
        description = "Group under which Safeticket Mailer runs.";
      };

      configFile = mkOption {
        type = path;
        description = "Path to the configuration file for Safeticket Mailer";
        example = ''pkgs.writeText "safeticket-mailer-config.py" (builtins.readFile ./config.py)'';
      };

      dataFolder = mkOption {
        type = path;
        default = "/var/lib/${username}";
        description = "Path to the folder in which Safeticket Mailer stores its data";
      };

      environmentFile = mkOption {
        type = lib.types.nullOr lib.types.path;
        default = null;
        description = "Environment file, used to set any secrets";
      };

      startAt = mkOption {
        type = either (str) (listOf str);
        description = ''
          When to start the Safeticket Mailer service.
          The example shows how to start it every Monday at 07:00 (AM).

          Read more the configuring
          [systemd.timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html).

          **Note:** This option is an alias for `systemd.services.<name>.startAt`.
        '';
        example = "Mon *-*-* 07:00:00";
      };
    };
  };
}
