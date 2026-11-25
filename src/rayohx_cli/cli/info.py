"""The ``info`` command: show what a stream offers without downloading it."""

import typer
from rayohx import MasterPlaylist, inspect, inspect_text, playlist_to_dict, select_stream
from rayohx.errors import ConfigurationError, RayoHXError

from rayohx_cli import output, params, render
from rayohx_cli.cli.common import EXIT_FAILED, make_config, open_source, usage_error
from rayohx_cli.cli.root import app


@app.command()
def info(
    url: params.Url,
    playlist_file: params.PlaylistFile = None,
    base_url: params.BaseUrl = None,
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
    credential_host: params.CredentialHost = None,
    json_output: params.JsonOutput = False,
) -> None:
    """Show what a stream offers, without downloading it.

    Lists the streams (size, bit rate, codecs), the audio and subtitle tracks, and which of them
    a download with the same options would pick (marked with *).
    """
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
        credential_host=credential_host or [],
    )
    try:
        source = open_source(url, base_url, playlist_file)
        playlist = (
            inspect(source.url, config.network)
            if source.text is None
            else inspect_text(source.text, source.url)
        )
        selection = (
            select_stream(playlist, config.selection)
            if isinstance(playlist, MasterPlaylist)
            else None
        )
    except ConfigurationError as exc:
        usage_error(exc)
    except RayoHXError as exc:
        output.error_from(exc)
        raise typer.Exit(EXIT_FAILED) from exc
    data = playlist_to_dict(playlist, selection)
    if json_output:
        output.print_json(data)
    else:
        render.show(data)
