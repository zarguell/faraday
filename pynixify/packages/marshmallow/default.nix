# WARNING: This file was automatically generated. You should avoid editing it.
# If you run pynixify again, the file will be either overwritten or
# deleted, and you will lose the changes you made to it.

{ buildPythonPackage
, fetchPypi
, lib
}:

buildPythonPackage rec {
  pname =
    "marshmallow";
  version =
    "3.12.2";

  src =
    fetchPypi {
      inherit
        pname
        version;
      sha256 =
        "1zyjjcscwhwa82424blyiihdihgs6c5wxnxv3h23lg6rvbz8sdkp";
    };

  # TODO FIXME
  doCheck =
    false;

  meta =
    with lib; {
      description =
        "A lightweight library for converting complex datatypes to and from native Python datatypes.";
      homepage =
        "https://github.com/marshmallow-code/marshmallow";
    };
}
