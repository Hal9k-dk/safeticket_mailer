{ lib
, python3Packages
, wkhtmltopdf
}:

with python3Packages;

buildPythonPackage rec {
  pname = "safeticket-mailer";
  version = "0.2.0";

  src = lib.sources.cleanSource ./.;

  # do not run tests
  doCheck = false;

  propagatedBuildInputs = [
    wkhtmltopdf

    pyyaml
    tabulate
    jinja2
    odfpy
    requests
  ];

#   configurePhase = ''
#     find
#     pwd
#     ls -la
#   '';

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  build-system =  [
    setuptools
    wheel
  ];

  meta = {
    mainProgram = "safeticket-mailer";
  };
}
