from datetime import datetime, timezone


class TemplateService:
    def render_metadata(self, template: dict, project: dict, audio: dict, export: dict, attribution_block: str) -> dict:
        metadata = dict(template.get("metadata", {}))

        variables = {
            "{project.title}": project.get("title", ""),
            "{project.artist}": project.get("artist", ""),
            "{project.series}": project.get("series", ""),
            "{project.genre}": project.get("genre", ""),
            "{audio.bpm}": str(audio.get("tempo_bpm", "")),
            "{audio.duration_sec}": str(audio.get("duration_sec", "")),
            "{export.fps}": str(export.get("fps", "")),
            "{export.width}": str(export.get("width", "")),
            "{export.height}": str(export.get("height", "")),
            "{export.duration_hms}": export.get("duration_hms", ""),
            "{provenance.attribution_block}": attribution_block or "",
            "{now.iso_date}": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

        def resolve(text: str) -> str:
            result = text
            for key, value in variables.items():
                result = result.replace(key, value)
            return result

        metadata["title"] = resolve(metadata.get("title", ""))
        metadata["description"] = resolve(metadata.get("description", ""))
        metadata["tags"] = [resolve(t) for t in metadata.get("tags", [])]
        metadata.setdefault("categoryId", "10")
        metadata.setdefault("privacyStatus", "private")
        metadata.setdefault("publishAt", None)
        metadata.setdefault("playlistIds", [])
        metadata.setdefault("chapters", [])

        return {
            "schema_version": 1,
            **metadata,
        }
