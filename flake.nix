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

            src = ./.;

            doCheck = false;
            propagatedBuildInputs = [ pkgs.python39.pkgs.colorama
            pkgs.python39.pkgs.pyaml pkgs.python39.pkgs.junit-xml];
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
