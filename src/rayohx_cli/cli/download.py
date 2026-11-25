"""The ``download`` command: save a stream to a file."""

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rayohx import Downloader, OutputFormat, RemuxBackend, StorageStrategy
from rayohx.errors import ConfigurationError

from rayohx_cli import output, params
from rayohx_cli.cli.common import (
    EXIT_CANCELLED,
    Source,
    gather_urls,
    make_config,
    open_source,
    usage_error,
)
from rayohx_cli.cli.lifecycle import finish, graceful_interrupt, pause_toggle
from rayohx_cli.cli.root import app
from rayohx_cli.progress import MODES, make_reporter

if TYPE_CHECKING:
    from rayohx.config import DownloadConfig


@app.command()
def download(
    urls: params.Urls = None,
    output_path: params.OutputPath = None,
    quality: params.Quality = "best",
    max_resolution: params.MaxResolution = None,
    max_bitrate: params.MaxBitrate = None,
    variant: params.Variant = None,
    resolution: params.Resolution = None,
    bandwidth: params.Bandwidth = None,
    variant_name: params.VariantName = None,
    codec: params.Codec = None,
    video_range: params.VideoRange = None,
    max_frame_rate: params.MaxFrameRate = None,
    audio: params.Audio = None,
    audio_name: params.AudioName = None,
    subtitles: params.Subtitles = None,
    subtitle_name: params.SubtitleName = None,
    video_only: params.VideoOnly = False,
    format_: params.Format = OutputFormat.AUTO,
    overwrite: params.Overwrite = False,
    validate: params.Validate = True,
    remux_backend: params.RemuxBackendOption = RemuxBackend.AUTO,
    ffmpeg: params.Ffmpeg = None,
    header: params.Header = None,
    cookie: params.Cookie = None,
    user_agent: params.UserAgent = None,
    referer: params.Referer = None,
    origin: params.Origin = None,
    proxy: params.Proxy = None,
    proxy_username: params.ProxyUsername = None,
    proxy_password: params.ProxyPassword = None,
    backoff: params.Backoff = None,
    max_redirects: params.MaxRedirects = None,
    cookie_file: params.CookieFile = None,
    insecure: params.Insecure = False,
    ca_bundle: params.CaBundle = None,
    env_proxy: params.EnvProxy = False,
    client_cert: params.ClientCert = None,
    client_key: params.ClientKey = None,
    client_key_password: params.ClientKeyPassword = None,
    connect_timeout: params.ConnectTimeout = None,
    read_timeout: params.ReadTimeout = None,
    timeout: params.Timeout = None,
    retries: params.Retries = None,
    rate_limit: params.RateLimit = None,
    credential_host: params.CredentialHost = None,
    concurrency: params.Concurrency = None,
    resume: params.Resume = True,
    storage: params.Storage = StorageStrategy.AUTO,
    workspace: params.Workspace = None,
    buffer_size: params.BufferSize = None,
    max_temp_size: params.MaxTempSize = None,
    space_check: params.SpaceCheck = True,
    reserve_space: params.ReserveSpace = None,
    keep_state: params.KeepState = True,
    directory: params.Directory = None,
    allow_file_keys: params.AllowFileKeys = False,
    json_output: params.JsonOutput = False,
    progress: params.ProgressMode = "auto",
    input_file: params.InputFile = None,
    playlist_file: params.PlaylistFile = None,
    base_url: params.BaseUrl = None,
    events: params.Events = False,
    stop_on_error: params.StopOnError = False,
) -> None:
    """Download one or more streams to files.

    The path of each saved file is printed on stdout. With several addresses (or --input-file),
    --output names a folder and the files are named after the addresses. Interrupted downloads
    continue where they stopped when you run the same command again. Press Ctrl-C once to stop
    cleanly.
    """
    if progress not in MODES:
        raise typer.BadParameter(f"must be one of {', '.join(MODES)}.", param_hint="--progress")
    config = make_config(
        quality=quality,
        max_resolution=max_resolution,
        max_bitrate=max_bitrate,
        variant=variant,
        resolution=resolution,
        bandwidth=bandwidth,
        variant_name=variant_name,
        codec=codec,
        video_range=video_range,
        max_frame_rate=max_frame_rate,
        audio=audio or [],
        audio_name=audio_name or [],
        subtitles=subtitles or [],
        subtitle_name=subtitle_name or [],
        video_only=video_only,
        format=format_,
        overwrite=overwrite,
        validate=validate,
        remux_backend=remux_backend,
        ffmpeg=ffmpeg,
        header=header or [],
        cookie=cookie or [],
        user_agent=user_agent,
        referer=referer,
        origin=origin,
        proxy=proxy,
        proxy_username=proxy_username,
        proxy_password=proxy_password,
        backoff=backoff,
        max_redirects=max_redirects,
        cookie_file=cookie_file,
        insecure=insecure,
        ca_bundle=ca_bundle,
        env_proxy=env_proxy,
        client_cert=client_cert,
        client_key=client_key,
        client_key_password=client_key_password,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        timeout=timeout,
        retries=retries,
        rate_limit=rate_limit,
        credential_host=credential_host or [],
        concurrency=concurrency,
        resume=resume,
        storage=storage,
        workspace=workspace,
        buffer_size=buffer_size,
        max_temp_size=max_temp_size,
        space_check=space_check,
        reserve_space=reserve_space,
        keep_state=keep_state,
        directory=directory,
        allow_file_keys=allow_file_keys,
    )
    targets = gather_urls(urls or [], input_file)
    if playlist_file is not None and len(targets) > 1:
        usage_error(
            ConfigurationError(
                "--playlist-file works with one address.",
                hint="Give the address the playlist came from, and nothing else.",
            )
        )
    sources = [open_source(t, base_url, playlist_file) for t in targets]
    if events:
        progress = "none"
    if directory is not None:
        directory.mkdir(parents=True, exist_ok=True)
        if len(targets) > 1 and output_path is None:
            output_path = directory
    if len(targets) == 1:
        run_one(sources[0], output_path, config, progress, json_output, events=events)
        return
    run_many(sources, output_path, config, progress, json_output, stop_on_error, events)


def run_one(
    source: Source,
    output_path: Path | None,
    config: "DownloadConfig",
    progress: str,
    json_output: bool,
    documents: list[dict[str, object]] | None = None,
    downloader: Downloader | None = None,
    events: bool = False,
) -> None:
    """Download one address with a progress display, then report how it ended."""
    try:
        downloader = downloader or Downloader(
            source.url, output=output_path, config=config, playlist_text=source.text
        )
    except ConfigurationError as exc:
        usage_error(exc)
    reporter = make_reporter(
        progress,
        output.err_console,
        quiet=output.settings.quiet,
        json_output=json_output,
        verbose=output.settings.verbose,
    )
    downloader.events.subscribe(reporter)
    if events:
        from rayohx_cli.events import EventStream

        downloader.events.subscribe(EventStream())
    reporter.start()
    try:
        with graceful_interrupt(downloader), pause_toggle(downloader):
            result = downloader.run()
    finally:
        reporter.close()
    finish(result, downloader, json_output=json_output, documents=documents)


def run_many(
    targets: list[Source],
    output_path: Path | None,
    config: "DownloadConfig",
    progress: str,
    json_output: bool,
    stop_on_error: bool,
    events: bool = False,
) -> None:
    """Download several addresses in turn into one folder."""
    from rayohx import batch_outputs

    if output_path is not None and output_path.exists() and not output_path.is_dir():
        usage_error(
            ConfigurationError(
                f"{output_path} is a file, but there are {len(targets)} addresses to download.",
                hint="With several addresses, --output names a folder.",
            )
        )
    paths = batch_outputs([source.url for source in targets], output_path)
    # Check every address and setting before anything is downloaded.
    try:
        downloaders = [
            Downloader(s.url, output=p, config=config, playlist_text=s.text)
            for s, p in zip(targets, paths, strict=True)
        ]
    except ConfigurationError as exc:
        usage_error(exc)
    if output_path is not None:
        output_path.mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, object]] = []
    code = 0
    for position, (source, downloader) in enumerate(
        zip(targets, downloaders, strict=True), start=1
    ):
        output.message(f"[{position}/{len(targets)}] {source.label}")
        try:
            run_one(source, None, config, progress, json_output, documents, downloader, events)
        except typer.Exit as exit_:
            code = EXIT_CANCELLED if exit_.exit_code == EXIT_CANCELLED else code or exit_.exit_code
            if exit_.exit_code == EXIT_CANCELLED or stop_on_error:
                break
    if json_output:
        output.print_json(documents)
    if code:
        raise typer.Exit(code)
