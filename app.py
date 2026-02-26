from pathlib import Path

import gradio as gr

from subtitle_pipeline import LANGUAGE_OPTIONS, SubtitleConfig, generate_srt


def _read_text(path: str | None):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def run_pipeline(
    audio_file,
    transcript_file,
    language_label,
    split_gap,
    merge_gap,
    max_chars_per_line,
    padding,
    model_size,
):
    if not audio_file:
        raise gr.Error("Audio file is required.")

    cfg = SubtitleConfig(
        language=LANGUAGE_OPTIONS[language_label],
        split_gap=float(split_gap),
        merge_gap=float(merge_gap),
        max_chars_per_line=int(max_chars_per_line),
        padding=float(padding),
        model_size=model_size,
    )
    transcript_text = _read_text(transcript_file)

    srt_path, cache_path, cache_hit = generate_srt(
        audio_path=audio_file,
        transcript_text=transcript_text,
        cfg=cfg,
        cache_dir="./cache",
    )

    status = (
        f"SRT generated successfully. {'Cache hit' if cache_hit else 'Fresh inference'}\n"
        f"Alignment/Transcription cache file: {Path(cache_path).name}"
    )
    return status, srt_path


with gr.Blocks(title="Instagram SRT Generator") as app:
    gr.Markdown(
        """
        # Instagram Subtitle Generator (stable-ts)
        Upload an audio file, optionally provide a transcript for alignment,
        tune segmentation settings, and download a production-ready SRT.
        """
    )

    with gr.Row():
        audio_file = gr.Audio(type="filepath", label="Audio file (required)")
        transcript_file = gr.File(label="Transcript .txt (optional)", file_types=[".txt"])

    with gr.Row():
        language_label = gr.Dropdown(
            choices=list(LANGUAGE_OPTIONS.keys()),
            value="English",
            label="Speech language",
            info="Used for transcription/alignment and line balancing rules.",
        )
        model_size = gr.Dropdown(
            choices=["tiny", "base", "small", "medium"],
            value="small",
            label="Whisper model size",
            info="Smaller is faster, larger can improve quality.",
        )

    with gr.Accordion("Advanced subtitle segmentation settings", open=False):
        split_gap = gr.Slider(0.1, 2.0, value=0.5, step=0.05, label="Split silence threshold (seconds)")
        merge_gap = gr.Slider(0.05, 1.0, value=0.15, step=0.05, label="Merge silence threshold (seconds)")
        max_chars_per_line = gr.Slider(18, 48, value=26, step=1, label="Max characters per subtitle line")
        padding = gr.Slider(0.0, 2.0, value=1.0, step=0.1, label="Subtitle end padding (seconds)")

    run_btn = gr.Button("Generate SRT", variant="primary")
    status = gr.Textbox(label="Run status", interactive=False)
    output_file = gr.File(label="Download .srt")

    run_btn.click(
        fn=run_pipeline,
        inputs=[audio_file, transcript_file, language_label, split_gap, merge_gap, max_chars_per_line, padding, model_size],
        outputs=[status, output_file],
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
