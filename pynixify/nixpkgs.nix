# WARNING: This file was automatically generated. You should avoid editing it.
# If you run pynixify again, the file will be either overwritten or
# deleted, and you will lose the changes you made to it.

{ overlays ?
  [ ]
, ...
}@args:
let
  pynixifyOverlay =
    self: super: {
      python2 =
        super.python2.override {
          inherit
            packageOverrides;
        };
      python27 =
        super.python27.override {
          inherit
            packageOverrides;
        };
      python3 =
        super.python3.override {
          inherit
            packageOverrides;
        };
      python35 =
        super.python35.override {
          inherit
            packageOverrides;
        };
      python36 =
        super.python36.override {
          inherit
            packageOverrides;
        };
      python37 =
        super.python37.override {
          inherit
            packageOverrides;
        };
      python38 =
        super.python38.override {
          inherit
            packageOverrides;
        };
      python39 =
        super.python39.override {
          inherit
            packageOverrides;
        };
      python310 =
        super.python310.override {
          inherit
            packageOverrides;
        };
    };

  nixpkgs =

    builtins.fetchTarball {
      url =
        "https://github.com/infobyte/nixpkgs/archive/98720fe237de55ca5779af5ee07407d0947b8deb.tar.gz";
      sha256 =
        "1zfc84xg7xa70v3gfqn1wgzq0rn8fwna9bmmyi9720vs0bzkdj86";
    };

  packageOverrides =
    self: super: {
      anyascii =
        self.callPackage
        ./packages/anyascii
        { };

      apispec-webframeworks =
        self.callPackage
        ./packages/apispec-webframeworks
        { };

      bidict =
        self.callPackage
        ./packages/bidict
        { };

      bleach =
        self.callPackage
        ./packages/bleach
        { };

      click =
        self.callPackage
        ./packages/click
        { };

      cvss =
        self.callPackage
        ./packages/cvss
        { };

      faraday-agent-parameters-types =
        self.callPackage
        ./packages/faraday-agent-parameters-types
        { };

      faraday-plugins =
        self.callPackage
        ./packages/faraday-plugins
        { };

      faradaysec =
        self.callPackage
        ./packages/faradaysec
        { };

      filedepot =
        self.callPackage
        ./packages/filedepot
        { };

      filteralchemy-fork =
        self.callPackage
        ./packages/filteralchemy-fork
        { };

      flask-classful =
        self.callPackage
        ./packages/flask-classful
        { };

      flask-kvsession-fork =
        self.callPackage
        ./packages/flask-kvsession-fork
        { };

      flask-security-too =
        self.callPackage
        ./packages/flask-security-too
        { };

      flask-socketio =
        self.callPackage
        ./packages/flask-socketio
        { };

      flask-wtf =
        self.callPackage
        ./packages/flask-wtf
        { };

      marshmallow =
        self.callPackage
        ./packages/marshmallow
        { };

      marshmallow-sqlalchemy =
        self.callPackage
        ./packages/marshmallow-sqlalchemy
        { };

      pyjwt =
        self.callPackage
        ./packages/pyjwt
        { };

      pyotp =
        self.callPackage
        ./packages/pyotp
        { };

      python-engineio =
        self.callPackage
        ./packages/python-engineio
        { };

      python-socketio =
        self.callPackage
        ./packages/python-socketio
        { };

      simplekv =
        self.callPackage
        ./packages/simplekv
        { };

      syslog-rfc5424-formatter =
        self.callPackage
        ./packages/syslog-rfc5424-formatter
        { };

      webargs =
        self.callPackage
        ./packages/webargs
        { };

    };

in import
nixpkgs
(args
  // {
    overlays =
      [
        pynixifyOverlay
      ]
      ++ overlays;
  })
