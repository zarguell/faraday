# WARNING: This file was automatically generated. You should avoid editing it.
# If you run pynixify again, the file will be either overwritten or
# deleted, and you will lose the changes you made to it.

{ buildPythonPackage
, fetchPypi
, lib
, marshmallow
, packaging
, pytestrunner
}:

buildPythonPackage rec {
  pname =
    "faraday-agent-parameters-types";
  version =
    "1.1.0";

  src =
    fetchPypi {
      inherit
        version;
      pname =
        "faraday_agent_parameters_types";
      sha256 =
        "0a0bzld9rmar4grrj9l21ypa6p6jg0xqxg9synrpnd58z9i3j87c";
    };

  buildInputs =
    [
      pytestrunner
    ];
  propagatedBuildInputs =
    [
      marshmallow
      packaging
    ];

  # TODO FIXME
  doCheck =
    false;

  meta =
    with lib; {
      description =
        ''
          The faraday agents run code remotely to ensure your domains. This info is triggered and published
              to a faraday server instance, which had set the parameters of the code. This repository sets the models to be used
              by both sides.'';
      homepage =
        "https://github.com/infobyte/faraday_agent_parameters_types";
    };
}
