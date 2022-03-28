{
  description = "Flake for the Refery package";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        refery =
          pkgs.python39Packages.buildPythonPackage rec {
            pname = "refery";
            version = "1.0.2";

            src = pkgs.python39Packages.fetchPypi {
              inherit pname version;
              sha256 = "5c658b424d5db3fd0349760d10a9cd3eb1a7acb974946ec1473fdc4eb923cd4b";
            };

            doCheck = false;
            propagatedBuildInputs = [ pkgs.python39.pkgs.colorama pkgs.python39.pkgs.pyaml];
            meta = with pkgs.lib; {
              homepage = "https://github.com/RostanTabet/refery";
              description = "A simple functional testing tool";
              license = licenses.mit;
              maintainers = with maintainers; [ RostanTabet ];
            };
          };
      in
        {
          defaultPackage = refery;
        }
    );
}
