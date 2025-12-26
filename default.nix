{
  lib,
  python3,
}:
python3.pkgs.buildPythonApplication {
  pname = "web-noise";
  version = "2.0.0";

  pyproject = true;

  src = ./.;

  build-system = with python3.pkgs; [
    setuptools
  ];

  dependencies = with python3.pkgs; [
    requests
    urllib3
  ];

  # Copy data files alongside the script
  postInstall = ''
    install -Dm644 ${./browser_profiles.json} $out/share/web-noise/browser_profiles.json
    install -Dm644 ${./config.example.json} $out/share/web-noise/config.example.json
  '';

  doCheck = false;

  meta = with lib; {
    description = "Generate realistic web traffic noise for privacy";
    longDescription = ''
      A tool that generates realistic-looking random web traffic to obfuscate
      browsing patterns. Supports multiple concurrent simulated users with
      real browser profiles and headers.
    '';
    homepage = "https://github.com/aciddemon/web-noise";
    license = licenses.mit;
    maintainers = with maintainers; [aciddemon];
    platforms = platforms.unix;
    mainProgram = "web-noise";
    sourceProvenance = with sourceTypes; [fromSource];
  };
}
