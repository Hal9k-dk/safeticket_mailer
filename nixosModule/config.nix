{ config
, lib
, ...
}: let

  cfg = config.services.safeticket-mailer;

in lib.mkIf cfg.enable {
  systemd = {
    tmpfiles.settings.navidromeDirs = {
      "${cfg.dataFolder}"."d" = {
        inherit (cfg) user group;
        mode = "700";
      };
    };

    services.safeticket-mailer = {
      startAt = cfg.startAt;

      description = "Safeticket Mailer";
      after = [ "network.target" ];
      serviceConfig = {
        ExecStart = ''
          ${lib.getExe cfg.package} \
            --config-file "${cfg.configFile}" \
            --data-folder "${cfg.dataFolder}" \
            --auto-include-past \
            --use-manual-ticket \
            --show-emails ${lib.optionalString cfg.sendEmails "--send-emails --send-invoice"}
        '';
        EnvironmentFile = lib.mkIf (cfg.environmentFile != null) [ cfg.environmentFile ];
        User = cfg.user;
        Group = cfg.group;

        # ReadWritePaths = "";
        # BindPaths =
        #   optional (cfg.settings ? DataFolder) cfg.settings.DataFolder
        #   ++ optional (cfg.settings ? CacheFolder) cfg.settings.CacheFolder;
        # BindReadOnlyPaths =
        #   [
        #     # navidrome uses online services to download additional album metadata / covers
        #     "${config.security.pki.caBundle}:/etc/ssl/certs/ca-certificates.crt"
        #     builtins.storeDir
        #     "/etc"
        #   ]
        #   ++ optional (cfg.settings ? MusicFolder) cfg.settings.MusicFolder
        #   ++ lib.optionals config.services.resolved.enable [
        #     "/run/systemd/resolve/stub-resolv.conf"
        #     "/run/systemd/resolve/resolv.conf"
        #   ];

        RestrictNamespaces = true;
        PrivateDevices = true;
        PrivateUsers = true;
        ProtectClock = true;
        ProtectControlGroups = true;
        ProtectHome = true;
        ProtectKernelLogs = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        SystemCallArchitectures = "native";
        SystemCallFilter = [
          "@system-service"
          "~@privileged"
        ];
        RestrictRealtime = true;
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
        UMask = "0066";
        ProtectHostname = true;
      };
    };
  };

  users.users."${cfg.user}" = {
    inherit (cfg) group;
    isSystemUser = true;
    createHome = true;
  };

  users.groups."${cfg.group}" = { };
}
