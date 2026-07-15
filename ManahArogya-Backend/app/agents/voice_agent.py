from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import Agent, WorkerOptions, cli
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, sarvam, silero

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
VOICE_AGENT_NAME = "mental-health-voice"
GREETING_PLAYBACK_DELAY_SECONDS = 0.6
EMOTION_CONTEXT_TOPIC = "emotion-context"
INITIAL_EMOTION_WAIT_SECONDS = 5.0


async def _sarvam_run_with_mp3_output(self, output_emitter) -> None:
    request_id = sarvam.tts.utils.shortuuid()
    self._client_request_id = request_id
    self._server_request_id = None
    output_emitter.initialize(
        request_id=request_id,
        sample_rate=self._opts.speech_sample_rate,
        num_channels=1,
        mime_type="audio/mpeg",
        stream=True,
        frame_size_ms=50,
    )

    async def _tokenize_input() -> None:
        word_stream = None
        async for input_value in self._input_ch:
            if isinstance(input_value, str):
                if word_stream is None:
                    tokenizer_instance = (
                        self._opts.word_tokenizer
                        if self._opts.word_tokenizer is not None
                        else sarvam.tts.tokenize.basic.SentenceTokenizer()
                    )
                    word_stream = tokenizer_instance.stream()
                    self._segments_ch.send_nowait(word_stream)
                word_stream.push_text(input_value)
            elif isinstance(input_value, self._FlushSentinel):
                if word_stream:
                    word_stream.end_input()
                word_stream = None

        if word_stream is not None:
            word_stream.end_input()

        self._segments_ch.close()

    async def _process_segments() -> None:
        async for word_stream in self._segments_ch:
            await self._run_ws(word_stream, output_emitter)

    tasks = [
        asyncio.create_task(_tokenize_input()),
        asyncio.create_task(_process_segments()),
    ]
    try:
        await asyncio.gather(*tasks)
    except (
        sarvam.tts.APIStatusError,
        sarvam.tts.APIConnectionError,
        sarvam.tts.APITimeoutError,
    ):
        raise
    except asyncio.TimeoutError:
        raise sarvam.tts.APITimeoutError() from None
    except sarvam.tts.aiohttp.ClientResponseError as exc:
        raise sarvam.tts.APIStatusError(
            message=exc.message,
            status_code=exc.status,
            request_id=request_id,
            body=None,
        ) from None
    except Exception as exc:
        raise sarvam.tts.APIConnectionError(f"TTS stream failed: {exc}") from exc
    finally:
        await sarvam.tts.utils.aio.gracefully_cancel(*tasks)
        output_emitter.end_input()


sarvam.tts.SynthesizeStream._run = _sarvam_run_with_mp3_output

LANGUAGE_PROFILES = {
    "en-IN": {"label": "English", "instruction_name": "English"},
    "hi-IN": {"label": "Hindi", "instruction_name": "Hindi"},
    "bn-IN": {"label": "Bengali", "instruction_name": "Bengali"},
    "ta-IN": {"label": "Tamil", "instruction_name": "Tamil"},
    "te-IN": {"label": "Telugu", "instruction_name": "Telugu"},
    "kn-IN": {"label": "Kannada", "instruction_name": "Kannada"},
    "ml-IN": {"label": "Malayalam", "instruction_name": "Malayalam"},
    "mr-IN": {"label": "Marathi", "instruction_name": "Marathi"},
    "gu-IN": {"label": "Gujarati", "instruction_name": "Gujarati"},
    "pa-IN": {"label": "Punjabi", "instruction_name": "Punjabi"},
    "od-IN": {"label": "Odia", "instruction_name": "Odia"},
}

DOCTOR_PROFILES = {
    "depression": {
        "name": "Depression Specialist Agent",
        "specialty": "depression support",
        "focus": "low mood, hopelessness, burnout, and emotional numbness",
        "style": "use warm reassurance, help the user name feelings, and suggest very small next steps",
        "presence": "sound like a warm, confident doctor who gently lifts the patient's hope",
        "speaker": "simran",
    },
    "anxiety": {
        "name": "Anxiety Specialist Agent",
        "specialty": "anxiety support",
        "focus": "racing thoughts, overthinking, stress spikes, and panic-like feelings",
        "style": "slow the pace, guide breathing, and help the user return to the present moment",
        "presence": "sound like a calm doctor who immediately creates safety and steadiness",
        "speaker": "priya",
    },
    "stress": {
        "name": "Stress Specialist Agent",
        "specialty": "stress management",
        "focus": "pressure, overload, work stress, and emotional exhaustion",
        "style": "keep the advice practical, calming, and easy to follow in daily life",
        "presence": "sound like a composed doctor who is practical, grounded, and reassuring",
        "speaker": "simran",
    },
    "sleep": {
        "name": "Sleep Specialist Agent",
        "specialty": "sleep support",
        "focus": "restlessness, poor sleep, late-night worry, and fatigue",
        "style": "sound steady and restful, and suggest calming routines that feel realistic",
        "presence": "sound like a soft-spoken doctor with a restful and soothing bedside manner",
        "speaker": "rohan",
    },
    "trauma-support": {
        "name": "Trauma Support Agent",
        "specialty": "trauma-informed support",
        "focus": "emotional safety, grounding, overwhelm, and difficult memories",
        "style": "move gently, never push, prioritize safety, and offer grounding support first",
        "presence": "sound like a very careful doctor who speaks gently and respectfully",
        "speaker": "shreya",
    },
    "youth-care": {
        "name": "Student Support Agent",
        "specialty": "student and youth mental health",
        "focus": "academic pressure, confidence issues, loneliness, and routine stress",
        "style": "use simple encouraging language and give manageable suggestions",
        "presence": "sound like an approachable doctor who is supportive, positive, and easy to talk to",
        "speaker": "kavya",
    },
}

EXERCISE_PROFILES = {
    "calm-breathing": {
        "name": "Calm Breathing Coach",
        "focus": "guiding the user through a calm breathing exercise with precise, minimal instructions",
        "style": "keep every spoken line brief, soothing, and easy to follow",
        "presence": "sound like a grounded breathing coach who speaks slowly and reassuringly",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": "{user_name}, we are starting the calm breathing exercise now. Follow my voice and begin when I guide you.",
                "stages": {
                    "INHALE": {"label": "Breathe In", "instruction": "Breathe in slowly.", "spoken": "Breathe in slowly."},
                    "HOLD": {"label": "Hold", "instruction": "Hold your breath.", "spoken": "Hold your breath."},
                    "EXHALE": {"label": "Breathe Out", "instruction": "Breathe out slowly.", "spoken": "Breathe out slowly."},
                },
                "completion_line": "Exercise complete. Great job!",
            },
            "hi-IN": {
                "opening_line": "{user_name}, ab hum calm breathing exercise shuru kar rahe hain. Meri awaaz ke saath shuru kijiye.",
                "stages": {
                    "INHALE": {"label": "Saans Andar", "instruction": "Dheere se saans andar lijiye.", "spoken": "Dheere se saans andar lijiye."},
                    "HOLD": {"label": "Rok Kar Rakhiye", "instruction": "Saans ko roke rakhiye.", "spoken": "Saans ko roke rakhiye."},
                    "EXHALE": {"label": "Saans Bahar", "instruction": "Dheere se saans bahar chhodiye.", "spoken": "Dheere se saans bahar chhodiye."},
                },
                "completion_line": "Exercise poori ho gayi. Bahut achha kiya.",
            },
            "mr-IN": {
                "opening_line": "{user_name}, आता आपण calm breathing exercise सुरू करत आहोत. हळूवार श्वास आत घ्या.",
                "stages": {
                    "INHALE": {"label": "श्वास आत", "instruction": "हळूवार श्वास आत घ्या.", "spoken": "हळूवार श्वास आत घ्या."},
                    "HOLD": {"label": "धरा", "instruction": "श्वास रोखून धरा.", "spoken": "श्वास रोखून धरा."},
                    "EXHALE": {"label": "श्वास बाहेर", "instruction": "हळूवार श्वास बाहेर सोडा.", "spoken": "हळूवार श्वास बाहेर सोडा."},
                },
                "completion_line": "व्यायाम पूर्ण झाला. खूप छान केलंत.",
            },
        },
    },
    "anulom-vilom": {
        "name": "Anulom Vilom Coach",
        "focus": "guiding the user through anulom vilom (alternate nostril breathing) with calm, step-by-step cues",
        "style": "keep every spoken line brief, clear, and steady",
        "presence": "sound like a calm yoga breathing coach who speaks slowly and reassuringly",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": (
                    "{user_name}, let's begin Anulom Vilom breathing. "
                    "Sit comfortably with your back straight. Relax your shoulders, and gently close your eyes."
                ),
                "stages": {
                    "RIGHT_THUMB": {
                        "label": "Right Thumb",
                        "instruction": "Place your right thumb on your right nostril.",
                        "spoken": "Place your right thumb on your right nostril.",
                    },
                    "INHALE_LEFT": {
                        "label": "Inhale Left",
                        "instruction": "Close the right nostril, and inhale slowly through the left nostril.",
                        "spoken": "Close the right nostril, and inhale slowly through the left nostril.",
                    },
                    "EXHALE_RIGHT": {
                        "label": "Exhale Right",
                        "instruction": "Now close the left nostril, and gently exhale through the right nostril.",
                        "spoken": "Now close the left nostril, and gently exhale through the right nostril.",
                    },
                    "INHALE_RIGHT": {
                        "label": "Inhale Right",
                        "instruction": "Inhale through the right nostril.",
                        "spoken": "Now inhale through the right nostril.",
                    },
                    "EXHALE_LEFT": {
                        "label": "Exhale Left",
                        "instruction": "Close the right nostril, and exhale through the left nostril.",
                        "spoken": "Close the right nostril, and exhale through the left nostril.",
                    },
                    "LOOP": {
                        "label": "Continue",
                        "instruction": "Continue this breathing pattern slowly.",
                        "spoken": "Continue this breathing pattern slowly for the next one minute.",
                    },
                },
                "completion_line": "Great job. Slowly return to normal breathing.",
            },
            "hi-IN": {
                "opening_line": (
                    "{user_name}, अब हम अनुलोम विलोम शुरू करेंगे। "
                    "आराम से बैठिए, पीठ सीधी रखिए, कंधे ढीले छोड़िए और धीरे से आंखें बंद कीजिए।"
                ),
                "stages": {
                    "RIGHT_THUMB": {
                        "label": "दायां अंगूठा",
                        "instruction": "अपना दायां अंगूठा दायीं नासिका पर रखिए।",
                        "spoken": "अपना दायां अंगूठा दायीं नासिका पर रखिए।",
                    },
                    "INHALE_LEFT": {
                        "label": "बाएं से श्वास",
                        "instruction": "दायीं नासिका बंद करके बायीं नासिका से धीरे श्वास लीजिए।",
                        "spoken": "दायीं नासिका बंद करके बायीं नासिका से धीरे श्वास लीजिए।",
                    },
                    "EXHALE_RIGHT": {
                        "label": "दाएं से श्वास छोड़ें",
                        "instruction": "अब बायीं नासिका बंद करके दायीं नासिका से धीरे श्वास छोड़िए।",
                        "spoken": "अब बायीं नासिका बंद करके दायीं नासिका से धीरे श्वास छोड़िए।",
                    },
                    "INHALE_RIGHT": {
                        "label": "दाएं से श्वास",
                        "instruction": "दायीं नासिका से श्वास लीजिए।",
                        "spoken": "अब दायीं नासिका से श्वास लीजिए।",
                    },
                    "EXHALE_LEFT": {
                        "label": "बाएं से श्वास छोड़ें",
                        "instruction": "दायीं नासिका बंद करके बायीं नासिका से श्वास छोड़िए।",
                        "spoken": "दायीं नासिका बंद करके बायीं नासिका से श्वास छोड़िए।",
                    },
                    "LOOP": {
                        "label": "जारी रखें",
                        "instruction": "इसी क्रम को धीरे-धीरे जारी रखिए।",
                        "spoken": "अगले एक मिनट तक इसी श्वास क्रम को धीरे-धीरे जारी रखिए।",
                    },
                },
                "completion_line": "बहुत अच्छा। अब धीरे-धीरे सामान्य श्वास पर लौट आइए।",
            },
            "mr-IN": {
                "opening_line": (
                    "{user_name}, आता आपण अनुलोम विलोम सुरू करूया. "
                    "आरामात बसा, पाठ सरळ ठेवा, खांदे सैल सोडा आणि हळूच डोळे मिटा."
                ),
                "stages": {
                    "RIGHT_THUMB": {
                        "label": "उजवा अंगठा",
                        "instruction": "तुमचा उजवा अंगठा उजव्या नाकपुडीवर ठेवा.",
                        "spoken": "तुमचा उजवा अंगठा उजव्या नाकपुडीवर ठेवा.",
                    },
                    "INHALE_LEFT": {
                        "label": "डावीकडून श्वास",
                        "instruction": "उजवी नाकपुडी बंद करून डाव्या नाकपुडीतून हळूवार श्वास घ्या.",
                        "spoken": "उजवी नाकपुडी बंद करून डाव्या नाकपुडीतून हळूवार श्वास घ्या.",
                    },
                    "EXHALE_RIGHT": {
                        "label": "उजवीकडून श्वास सोडा",
                        "instruction": "आता डावी नाकपुडी बंद करून उजव्या नाकपुडीतून हळूवार श्वास सोडा.",
                        "spoken": "आता डावी नाकपुडी बंद करून उजव्या नाकपुडीतून हळूवार श्वास सोडा.",
                    },
                    "INHALE_RIGHT": {
                        "label": "उजवीकडून श्वास",
                        "instruction": "उजव्या नाकपुडीतून श्वास घ्या.",
                        "spoken": "आता उजव्या नाकपुडीतून श्वास घ्या.",
                    },
                    "EXHALE_LEFT": {
                        "label": "डावीकडून श्वास सोडा",
                        "instruction": "उजवी नाकपुडी बंद करून डाव्या नाकपुडीतून श्वास सोडा.",
                        "spoken": "उजवी नाकपुडी बंद करून डाव्या नाकपुडीतून श्वास सोडा.",
                    },
                    "LOOP": {
                        "label": "पुढे चालू",
                        "instruction": "हीच पद्धत हळूवार सुरू ठेवा.",
                        "spoken": "पुढील एक मिनिट हीच श्वासाची पद्धत हळूवार सुरू ठेवा.",
                    },
                },
                "completion_line": "छान केले. आता हळूहळू नेहमीच्या श्वासावर या.",
            }
        },
    },
    "bhramari-pranayama": {
        "name": "Bhramari Pranayama Coach",
        "focus": "guiding the user through bhramari pranayama (humming bee breathing) to relax the mind and reduce stress",
        "style": "keep every spoken line brief, soothing, and easy to follow",
        "presence": "sound like a calm breathing coach who speaks slowly and reassuringly",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": (
                    "{user_name}, we will now practice Bhramari breathing. "
                    "This exercise helps relax the brain and reduce stress. "
                    "Sit comfortably, and close your eyes."
                ),
                "stages": {
                    "INHALE": {
                        "label": "Inhale",
                         "instruction": "Take a deep breath in through your nose.",
                        "spoken": "Take a deep breath in through your nose.",
                    },
                    "HUM": {
                        "label": "Humming Exhale",
                        "instruction": "Now slowly exhale while making a gentle humming sound like a bee. Mmmmmmmmm.",
                        "spoken": "Now slowly exhale while making a gentle humming sound like a bee. Mmmmmmmmm.",
                    },
                    "VIBRATION": {
                        "label": "Feel the vibration",
                        "instruction": "Feel the vibration relaxing your mind.",
                        "spoken": "Feel the vibration relaxing your mind.",
                    },
                    "LOOP": {
                        "label": "Repeat",
                        "instruction": "Let's repeat this together five times.",
                        "spoken": "Let's repeat this together five times.",
                    },
                },
                "completion_line": "Take a normal breath and notice the calmness in your body.",
            },
            "hi-IN": {
                "opening_line": (
                    "{user_name}, अब हम भ्रामरी प्राणायाम करेंगे। "
                    "यह अभ्यास मन को शांत करने और तनाव कम करने में मदद करता है। "
                    "आराम से बैठिए और आंखें बंद कीजिए।"
                ),
                "stages": {
                    "INHALE": {
                        "label": "श्वास लें",
                        "instruction": "नाक से गहरी श्वास लीजिए।",
                        "spoken": "नाक से गहरी श्वास लीजिए।",
                    },
                    "HUM": {
                        "label": "गुनगुनाहट के साथ श्वास छोड़ें",
                        "instruction": "अब धीरे-धीरे श्वास छोड़ते हुए मधुमक्खी जैसी हल्की गुनगुनाहट कीजिए। म्म्म्म्म्म।",
                        "spoken": "अब धीरे-धीरे श्वास छोड़ते हुए मधुमक्खी जैसी हल्की गुनगुनाहट कीजिए। म्म्म्म्म्म।",
                    },
                    "VIBRATION": {
                        "label": "कंपन महसूस करें",
                        "instruction": "इस कंपन को महसूस कीजिए और मन को शांत होने दीजिए।",
                        "spoken": "इस कंपन को महसूस कीजिए और मन को शांत होने दीजिए।",
                    },
                    "LOOP": {
                        "label": "दोहराएं",
                        "instruction": "आइए इसे हम पांच बार साथ में दोहराएं।",
                        "spoken": "आइए इसे हम पांच बार साथ में दोहराएं।",
                    },
                },
                "completion_line": "सामान्य श्वास लीजिए और शरीर में शांति महसूस कीजिए।",
            },
            "mr-IN": {
                "opening_line": (
                    "{user_name}, आता आपण भ्रामरी प्राणायाम करूया. "
                    "हा सराव मन शांत करायला आणि ताण कमी करायला मदत करतो. "
                    "आरामात बसा आणि डोळे मिटा."
                ),
                "stages": {
                    "INHALE": {
                        "label": "श्वास घ्या",
                        "instruction": "नाकातून खोल श्वास घ्या.",
                        "spoken": "नाकातून खोल श्वास घ्या.",
                    },
                    "HUM": {
                        "label": "गुंजारवाने श्वास सोडा",
                        "instruction": "आता हळूवार श्वास सोडताना मधमाशीप्रमाणे हलका गुंजारव करा. म्म्म्म्म्म.",
                        "spoken": "आता हळूवार श्वास सोडताना मधमाशीप्रमाणे हलका गुंजारव करा. म्म्म्म्म्म.",
                    },
                    "VIBRATION": {
                        "label": "कंपन अनुभवा",
                        "instruction": "हे कंपन अनुभवा आणि मन शांत होऊ द्या.",
                        "spoken": "हे कंपन अनुभवा आणि मन शांत होऊ द्या.",
                    },
                    "LOOP": {
                        "label": "पुन्हा करा",
                        "instruction": "चला, हे आपण पाच वेळा एकत्र करूया.",
                        "spoken": "चला, हे आपण पाच वेळा एकत्र करूया.",
                    },
                },
                "completion_line": "सामान्य श्वास घ्या आणि शरीरातील शांतता अनुभवा.",
            }
        },
    },
    "balasana": {
        "name": "Child's Pose Coach",
        "focus": "guiding the user into balasana (child's pose) with gentle posture and breathing cues",
        "style": "keep every spoken line brief, calm, and easy to follow",
        "presence": "sound like a calm yoga coach who speaks slowly and reassuringly",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": (
                    "{user_name}, now we will move into Child’s Pose, a relaxing yoga posture."
                ),
                "stages": {
                    "KNEEL": {
                        "label": "Kneel",
                        "instruction": "Kneel on the floor.",
                        "spoken": "Kneel on the floor.",
                    },
                    "HEELS": {
                        "label": "Sit back",
                        "instruction": "Sit back on your heels.",
                        "spoken": "Sit back on your heels.",
                    },
                    "FOLD": {
                        "label": "Fold forward",
                        "instruction": "Slowly bend forward and stretch your arms in front of you.",
                        "spoken": "Slowly bend forward and stretch your arms in front of you.",
                    },
                    "FOREHEAD": {
                        "label": "Rest",
                        "instruction": "Rest your forehead on the floor.",
                        "spoken": "Rest your forehead on the floor.",
                    },
                    "BREATHE": {
                        "label": "Slow breaths",
                        "instruction": "Take slow deep breaths.",
                        "spoken": "Take slow deep breaths.",
                    },
                    "INHALE": {
                        "label": "Inhale",
                        "instruction": "Inhale slowly.",
                        "spoken": "Inhale slowly.",
                    },
                    "EXHALE": {
                        "label": "Exhale",
                        "instruction": "Exhale and relax your body.",
                        "spoken": "Exhale and relax your body.",
                    },
                    "HOLD": {
                        "label": "Hold",
                        "instruction": "Stay in this position for about one minute.",
                        "spoken": "Stay in this position for about one minute.",
                    },
                },
                "completion_line": "Gently lift your head and return to a sitting position.",
            },
            "hi-IN": {
                "opening_line": (
                    "{user_name}, अब हम बालासन करेंगे, यह एक आराम देने वाला योगासन है।"
                ),
                "stages": {
                    "KNEEL": {
                        "label": "घुटनों के बल आएं",
                        "instruction": "फर्श पर घुटनों के बल आ जाइए।",
                        "spoken": "फर्श पर घुटनों के बल आ जाइए।",
                    },
                    "HEELS": {
                        "label": "एड़ियों पर बैठें",
                        "instruction": "अपनी एड़ियों पर बैठ जाइए।",
                        "spoken": "अपनी एड़ियों पर बैठ जाइए।",
                    },
                    "FOLD": {
                        "label": "आगे झुकें",
                        "instruction": "धीरे से आगे झुकिए और अपने हाथ सामने फैलाइए।",
                        "spoken": "धीरे से आगे झुकिए और अपने हाथ सामने फैलाइए।",
                    },
                    "FOREHEAD": {
                        "label": "आराम",
                        "instruction": "अपना माथा फर्श पर टिकाइए।",
                        "spoken": "अपना माथा फर्श पर टिकाइए।",
                    },
                    "BREATHE": {
                        "label": "धीमी श्वास",
                        "instruction": "धीमी और गहरी श्वास लीजिए।",
                        "spoken": "धीमी और गहरी श्वास लीजिए।",
                    },
                    "INHALE": {
                        "label": "श्वास लें",
                        "instruction": "धीरे से श्वास लीजिए।",
                        "spoken": "धीरे से श्वास लीजिए।",
                    },
                    "EXHALE": {
                        "label": "श्वास छोड़ें",
                        "instruction": "श्वास छोड़िए और शरीर को ढीला छोड़ दीजिए।",
                        "spoken": "श्वास छोड़िए और शरीर को ढीला छोड़ दीजिए।",
                    },
                    "HOLD": {
                        "label": "रुकें",
                        "instruction": "करीब एक मिनट इसी स्थिति में बने रहिए।",
                        "spoken": "करीब एक मिनट इसी स्थिति में बने रहिए।",
                    },
                },
                "completion_line": "धीरे से सिर उठाइए और वापस बैठने की अवस्था में आइए।",
            },
            "mr-IN": {
                "opening_line": (
                    "{user_name}, आता आपण बालासन करूया. हे एक आराम देणारे योगासन आहे."
                ),
                "stages": {
                    "KNEEL": {
                        "label": "गुडघ्यांवर या",
                        "instruction": "जमिनीवर गुडघ्यांवर या.",
                        "spoken": "जमिनीवर गुडघ्यांवर या.",
                    },
                    "HEELS": {
                        "label": "टाचांवर बसा",
                        "instruction": "तुमच्या टाचांवर बसा.",
                        "spoken": "तुमच्या टाचांवर बसा.",
                    },
                    "FOLD": {
                        "label": "पुढे वाका",
                        "instruction": "हळूच पुढे वाका आणि हात समोर ताणा.",
                        "spoken": "हळूच पुढे वाका आणि हात समोर ताणा.",
                    },
                    "FOREHEAD": {
                        "label": "विश्रांती",
                        "instruction": "तुमचे कपाळ जमिनीवर ठेवा.",
                        "spoken": "तुमचे कपाळ जमिनीवर ठेवा.",
                    },
                    "BREATHE": {
                        "label": "हळू श्वास",
                        "instruction": "हळू आणि खोल श्वास घ्या.",
                        "spoken": "हळू आणि खोल श्वास घ्या.",
                    },
                    "INHALE": {
                        "label": "श्वास घ्या",
                        "instruction": "हळूवार श्वास घ्या.",
                        "spoken": "हळूवार श्वास घ्या.",
                    },
                    "EXHALE": {
                        "label": "श्वास सोडा",
                        "instruction": "श्वास सोडा आणि शरीर सैल करा.",
                        "spoken": "श्वास सोडा आणि शरीर सैल करा.",
                    },
                    "HOLD": {
                        "label": "थांबा",
                        "instruction": "सुमारे एक मिनिट या स्थितीत रहा.",
                        "spoken": "सुमारे एक मिनिट या स्थितीत रहा.",
                    },
                },
                "completion_line": "हळूच डोके उचला आणि पुन्हा बसण्याच्या स्थितीत या.",
            }
        },
    },
    "shavasana": {
        "name": "Shavasana Coach",
        "focus": "guiding the user through shavasana (deep relaxation) with gentle body-scan cues",
        "style": "keep every spoken line brief, slow, and soothing",
        "presence": "sound like a calm relaxation coach who speaks softly and steadily",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": "{user_name}, now we will practice Shavasana, a deep relaxation exercise.",
                "stages": {
                    "LIE_DOWN": {
                        "label": "Lie down",
                        "instruction": "Lie down on your back.",
                        "spoken": "Lie down on your back.",
                    },
                    "ARMS": {
                        "label": "Arms relaxed",
                        "instruction": "Keep your arms relaxed beside your body.",
                        "spoken": "Keep your arms relaxed beside your body.",
                    },
                    "CLOSE_EYES": {
                        "label": "Close your eyes",
                        "instruction": "Close your eyes.",
                        "spoken": "Close your eyes.",
                    },
                    "RELAX_FEET": {
                        "label": "Relax feet",
                        "instruction": "Relax your feet.",
                        "spoken": "Relax your feet.",
                    },
                    "RELAX_LEGS": {
                        "label": "Relax legs",
                        "instruction": "Relax your legs.",
                        "spoken": "Relax your legs.",
                    },
                    "RELAX_STOMACH": {
                        "label": "Relax stomach",
                        "instruction": "Relax your stomach.",
                        "spoken": "Relax your stomach.",
                    },
                    "RELAX_SHOULDERS": {
                        "label": "Relax shoulders",
                        "instruction": "Relax your shoulders.",
                        "spoken": "Relax your shoulders.",
                    },
                    "RELAX_FACE": {
                        "label": "Relax face",
                        "instruction": "Relax your face.",
                        "spoken": "Relax your face.",
                    },
                    "BREATHE": {
                        "label": "Slow breathing",
                        "instruction": "Take slow and gentle breaths.",
                        "spoken": "Take slow and gentle breaths.",
                    },
                },
                "completion_line": "Slowly move your fingers and open your eyes.",
            },
            "hi-IN": {
                "opening_line": "{user_name}, अब हम शवासन करेंगे, यह गहरी विश्रांति का अभ्यास है।",
                "stages": {
                    "LIE_DOWN": {
                        "label": "लेट जाएं",
                        "instruction": "पीठ के बल लेट जाइए।",
                        "spoken": "पीठ के बल लेट जाइए।",
                    },
                    "ARMS": {
                        "label": "बांहें ढीली",
                        "instruction": "अपनी बांहों को शरीर के पास आराम से रखिए।",
                        "spoken": "अपनी बांहों को शरीर के पास आराम से रखिए।",
                    },
                    "CLOSE_EYES": {
                        "label": "आंखें बंद",
                        "instruction": "अपनी आंखें बंद कीजिए।",
                        "spoken": "अपनी आंखें बंद कीजिए।",
                    },
                    "RELAX_FEET": {
                        "label": "पैर ढीले",
                        "instruction": "अपने पैरों को ढीला छोड़ दीजिए।",
                        "spoken": "अपने पैरों को ढीला छोड़ दीजिए।",
                    },
                    "RELAX_LEGS": {
                        "label": "टांगें ढीली",
                        "instruction": "अपनी टांगों को ढीला छोड़ दीजिए।",
                        "spoken": "अपनी टांगों को ढीला छोड़ दीजिए।",
                    },
                    "RELAX_STOMACH": {
                        "label": "पेट ढीला",
                        "instruction": "अपने पेट को ढीला छोड़ दीजिए।",
                        "spoken": "अपने पेट को ढीला छोड़ दीजिए।",
                    },
                    "RELAX_SHOULDERS": {
                        "label": "कंधे ढीले",
                        "instruction": "अपने कंधों को ढीला छोड़ दीजिए।",
                        "spoken": "अपने कंधों को ढीला छोड़ दीजिए।",
                    },
                    "RELAX_FACE": {
                        "label": "चेहरा ढीला",
                        "instruction": "अपने चेहरे को ढीला छोड़ दीजिए।",
                        "spoken": "अपने चेहरे को ढीला छोड़ दीजिए।",
                    },
                    "BREATHE": {
                        "label": "धीमी श्वास",
                        "instruction": "धीमी और सहज श्वास लीजिए।",
                        "spoken": "धीमी और सहज श्वास लीजिए।",
                    },
                },
                "completion_line": "धीरे-धीरे अपनी उंगलियां हिलाइए और आंखें खोलिए।",
            },
            "mr-IN": {
                "opening_line": "{user_name}, आता आपण शवासन करूया. हा खोल विश्रांतीचा सराव आहे.",
                "stages": {
                    "LIE_DOWN": {
                        "label": "झोपा",
                        "instruction": "पाठीवर झोपा.",
                        "spoken": "पाठीवर झोपा.",
                    },
                    "ARMS": {
                        "label": "हात सैल",
                        "instruction": "तुमचे हात शरीराच्या बाजूला आरामात ठेवा.",
                        "spoken": "तुमचे हात शरीराच्या बाजूला आरामात ठेवा.",
                    },
                    "CLOSE_EYES": {
                        "label": "डोळे मिटा",
                        "instruction": "तुमचे डोळे मिटा.",
                        "spoken": "तुमचे डोळे मिटा.",
                    },
                    "RELAX_FEET": {
                        "label": "पाय सैल",
                        "instruction": "तुमचे पाय सैल सोडा.",
                        "spoken": "तुमचे पाय सैल सोडा.",
                    },
                    "RELAX_LEGS": {
                        "label": "पायांचे स्नायू सैल",
                        "instruction": "तुमचे पाय सैल सोडा.",
                        "spoken": "तुमचे पाय सैल सोडा.",
                    },
                    "RELAX_STOMACH": {
                        "label": "पोट सैल",
                        "instruction": "तुमचे पोट सैल सोडा.",
                        "spoken": "तुमचे पोट सैल सोडा.",
                    },
                    "RELAX_SHOULDERS": {
                        "label": "खांदे सैल",
                        "instruction": "तुमचे खांदे सैल सोडा.",
                        "spoken": "तुमचे खांदे सैल सोडा.",
                    },
                    "RELAX_FACE": {
                        "label": "चेहरा सैल",
                        "instruction": "तुमचा चेहरा सैल सोडा.",
                        "spoken": "तुमचा चेहरा सैल सोडा.",
                    },
                    "BREATHE": {
                        "label": "हळू श्वास",
                        "instruction": "हळू आणि सहज श्वास घ्या.",
                        "spoken": "हळू आणि सहज श्वास घ्या.",
                    },
                },
                "completion_line": "हळूहळू बोटे हलवा आणि डोळे उघडा.",
            }
        },
    },
    "sukhasana-meditation": {
        "name": "Sukhasana Meditation Coach",
        "focus": "guiding the user through a short sukhasana meditation with steady posture and breath-awareness cues",
        "style": "keep every spoken line brief, calm, and easy to follow",
        "presence": "sound like a gentle meditation coach who speaks slowly and reassuringly",
        "speaker": "priya",
        "languages": {
            "en-IN": {
                "opening_line": "{user_name}, we will now practice a short meditation.",
                "stages": {
                    "SIT_CROSS_LEGGED": {
                        "label": "Sit comfortably",
                        "instruction": "Sit cross-legged comfortably.",
                        "spoken": "Sit cross-legged comfortably.",
                    },
                    "BACK_STRAIGHT": {
                        "label": "Back straight",
                        "instruction": "Keep your back straight.",
                        "spoken": "Keep your back straight.",
                    },
                    "HANDS_ON_KNEES": {
                        "label": "Hands on knees",
                        "instruction": "Rest your hands on your knees.",
                        "spoken": "Rest your hands on your knees.",
                    },
                    "CLOSE_EYES": {
                        "label": "Close your eyes",
                        "instruction": "Close your eyes.",
                        "spoken": "Close your eyes.",
                    },
                    "FOCUS_BREATH": {
                        "label": "Focus on breath",
                        "instruction": "Focus on your breathing.",
                        "spoken": "Focus on your breathing.",
                    },
                    "INHALE": {
                        "label": "Inhale",
                        "instruction": "Inhale slowly.",
                        "spoken": "Inhale slowly.",
                    },
                    "EXHALE": {
                        "label": "Exhale",
                        "instruction": "Exhale slowly.",
                        "spoken": "Exhale slowly.",
                    },
                    "RETURN_TO_BREATH": {
                        "label": "Return to breath",
                        "instruction": "If your thoughts wander, gently bring your attention back to your breath.",
                        "spoken": "If your thoughts wander, gently bring your attention back to your breath.",
                    },
                    "OPEN_EYES": {
                        "label": "Open your eyes",
                        "instruction": "Take a deep breath and slowly open your eyes.",
                        "spoken": "Take a deep breath and slowly open your eyes.",
                    },
                },
                "completion_line": "Meditation complete. Notice the calm in your body.",
            },
            "hi-IN": {
                "opening_line": "{user_name}, अब हम एक छोटी ध्यान प्रक्रिया करेंगे।",
                "stages": {
                    "SIT_CROSS_LEGGED": {
                        "label": "आराम से बैठें",
                        "instruction": "आराम से पालथी मारकर बैठिए।",
                        "spoken": "आराम से पालथी मारकर बैठिए।",
                    },
                    "BACK_STRAIGHT": {
                        "label": "पीठ सीधी",
                        "instruction": "अपनी पीठ सीधी रखिए।",
                        "spoken": "अपनी पीठ सीधी रखिए।",
                    },
                    "HANDS_ON_KNEES": {
                        "label": "हाथ घुटनों पर",
                        "instruction": "अपने हाथ घुटनों पर रखिए।",
                        "spoken": "अपने हाथ घुटनों पर रखिए।",
                    },
                    "CLOSE_EYES": {
                        "label": "आंखें बंद",
                        "instruction": "आंखें बंद कीजिए।",
                        "spoken": "आंखें बंद कीजिए।",
                    },
                    "FOCUS_BREATH": {
                        "label": "श्वास पर ध्यान",
                        "instruction": "अपनी श्वास पर ध्यान दीजिए।",
                        "spoken": "अपनी श्वास पर ध्यान दीजिए।",
                    },
                    "INHALE": {
                        "label": "श्वास लें",
                        "instruction": "धीरे से श्वास लीजिए।",
                        "spoken": "धीरे से श्वास लीजिए।",
                    },
                    "EXHALE": {
                        "label": "श्वास छोड़ें",
                        "instruction": "धीरे से श्वास छोड़िए।",
                        "spoken": "धीरे से श्वास छोड़िए।",
                    },
                    "RETURN_TO_BREATH": {
                        "label": "श्वास पर लौटें",
                        "instruction": "अगर मन भटके, तो धीरे से ध्यान वापस अपनी श्वास पर ले आइए।",
                        "spoken": "अगर मन भटके, तो धीरे से ध्यान वापस अपनी श्वास पर ले आइए।",
                    },
                    "OPEN_EYES": {
                        "label": "आंखें खोलें",
                        "instruction": "एक गहरी श्वास लीजिए और धीरे से आंखें खोलिए।",
                        "spoken": "एक गहरी श्वास लीजिए और धीरे से आंखें खोलिए।",
                    },
                },
                "completion_line": "ध्यान पूरा हुआ। अपने शरीर में शांति महसूस कीजिए।",
            },
            "mr-IN": {
                "opening_line": "{user_name}, आता आपण थोडेसे ध्यान करूया.",
                "stages": {
                    "SIT_CROSS_LEGGED": {
                        "label": "आरामात बसा",
                        "instruction": "आरामात पद्मासनासारखे बसून घ्या.",
                        "spoken": "आरामात पद्मासनासारखे बसून घ्या.",
                    },
                    "BACK_STRAIGHT": {
                        "label": "पाठ सरळ",
                        "instruction": "तुमची पाठ सरळ ठेवा.",
                        "spoken": "तुमची पाठ सरळ ठेवा.",
                    },
                    "HANDS_ON_KNEES": {
                        "label": "हात गुडघ्यांवर",
                        "instruction": "तुमचे हात गुडघ्यांवर ठेवा.",
                        "spoken": "तुमचे हात गुडघ्यांवर ठेवा.",
                    },
                    "CLOSE_EYES": {
                        "label": "डोळे मिटा",
                        "instruction": "डोळे मिटा.",
                        "spoken": "डोळे मिटा.",
                    },
                    "FOCUS_BREATH": {
                        "label": "श्वासावर लक्ष",
                        "instruction": "तुमच्या श्वासावर लक्ष द्या.",
                        "spoken": "तुमच्या श्वासावर लक्ष द्या.",
                    },
                    "INHALE": {
                        "label": "श्वास घ्या",
                        "instruction": "हळूवार श्वास घ्या.",
                        "spoken": "हळूवार श्वास घ्या.",
                    },
                    "EXHALE": {
                        "label": "श्वास सोडा",
                        "instruction": "हळूवार श्वास सोडा.",
                        "spoken": "हळूवार श्वास सोडा.",
                    },
                    "RETURN_TO_BREATH": {
                        "label": "श्वासाकडे परत या",
                        "instruction": "जर मन भरकटले, तर हळूच लक्ष पुन्हा श्वासाकडे आणा.",
                        "spoken": "जर मन भरकटले, तर हळूच लक्ष पुन्हा श्वासाकडे आणा.",
                    },
                    "OPEN_EYES": {
                        "label": "डोळे उघडा",
                        "instruction": "एक खोल श्वास घ्या आणि हळूच डोळे उघडा.",
                        "spoken": "एक खोल श्वास घ्या आणि हळूच डोळे उघडा.",
                    },
                },
                "completion_line": "ध्यान पूर्ण झाले. शरीरातील शांतता अनुभवा.",
            }
        },
    },
}

AGENT_GREETING_TEMPLATES = {
    "depression": {
        "en-IN": (
            "Hi {user_name},   how are you? Don’t worry,   I’m here with you. Are you feeling a bit low these days?  Tell me,   what’s going on?"
        ),
        "mr-IN": (
            "हाय {user_name}, कसा आहेस?  काळजी करू नकोस, आपण शांतपणे बोलूया. तुला थोडंसं depressed झाल्यासारखं वाटतंय,बरोबर ना? मला सांग,नेमकं काय चाललंय तुझ्या मनात?"
        ),
    },
    "anxiety": {
        "en-IN": (
            "Hi {user_name}, I’m here with you. Don’t worry, we’ll take this slowly. "
        "Just breathe for a moment. "
        "Can you tell me what’s making you feel anxious right now?"
        ),
        "mr-IN": (
            "हाय {user_name}, मी तुझ्यासोबत आहे. काळजी करू नकोस, चल, आधी थोडं शांत होऊ. "
        "एकदा शांतपणे श्वास घे. "
        "सांग , आत्ता तुला नेमकं कशामुळे अस्वस्थ वाटतंय?"
        ),
    },
    "stress": {
        "en-IN": (
            "Hi {user_name}, I’m here with you. Don’t worry, we’ll figure this out step by step. "
        "What’s been stressing you out the most lately?"
        ),
        "mr-IN": (
             "हाय {user_name}, मी तुझ्यासोबत आहे. काळजी करू नकोस, आपण हे हळूहळू समजून घेऊ. "
        "सध्या तुला सगळ्यात जास्त ताण कशामुळे येतोय?"
        ),
    },
    "sleep": {
        "en-IN": (
            "Hi {user_name}, I’m here with you. Let’s keep this simple and calm. "
        "Have you been able to sleep well the past few nights?"
        ),
        "mr-IN": (
            "हाय {user_name}, मी तुझ्यासोबत आहे. थोडं रिलॅक्स होऊया. "
        "गेल्या काही दिवसांत तुला नीट झोप लागतेय का?"
        ),
    },
    "trauma-support": {
        "en-IN": (
             "Hi {user_name}, I’m here with you. Take your time, there’s no rush. "
        "You can share only what you feel comfortable with. "
        "What would you like to talk about first?"
        ),
        "mr-IN": (
            "हाय {user_name}, मी तुझ्यासोबत आहे. घाई नाही, तू तुझ्या सोयीने बोलू शकतोस. "
        "तुला जेवढं आरामदायक वाटेल तेवढंच शेअर कर. "
        "सुरुवात कुठून करायची आहे तुला?"
        ),
    },
    "youth-care": {
        "en-IN": (
            "Hey {user_name}, I’m here with you. No need to stress, we can figure things out together. "
        "What’s been bothering you the most these days?"
        ),
        "mr-IN": (
            "हाय {user_name}, मी इथेच आहे. खूप टेन्शन घेऊ नकोस. "
        "सांग ना, सध्या काय चाललंय मनात?"
        ),
    },
}

DEFAULT_GREETING_TEMPLATE = {
    "en-IN": "Hello {user_name}. I am your {agent_name}. I am glad you are here today. How are you feeling right now?",
    "mr-IN": "नमस्कार {user_name}. मी तुमचा {agent_name} आहे. तुम्ही आज इथे आला आहात याचा मला आनंद आहे. आत्ता तुम्हाला कसं वाटतंय?",
}


@dataclass(slots=True)
class EmotionContext:
    availability: str = "unavailable"
    primary_emotion: str = ""
    confidence: float | None = None
    trend: str = "stable"
    sample_count: int | None = None
    window_ms: int | None = None
    observed_at: int | None = None


def _coerce_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_emotion_context(payload: dict[str, object]) -> EmotionContext:
    availability = str(payload.get("availability") or "").strip().lower()
    primary_emotion = (
        str(payload.get("primaryEmotion") or payload.get("primary_emotion") or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    trend = str(payload.get("trend") or "stable").strip().lower()

    if availability == "unavailable" or not primary_emotion:
        return EmotionContext(availability="unavailable")

    return EmotionContext(
        availability="available",
        primary_emotion=primary_emotion,
        confidence=_coerce_float(payload.get("confidence")),
        trend=trend or "stable",
        sample_count=_coerce_int(payload.get("sampleCount") or payload.get("sample_count")),
        window_ms=_coerce_int(payload.get("windowMs") or payload.get("window_ms")),
        observed_at=_coerce_int(payload.get("observedAt") or payload.get("observed_at")),
    )


def _build_doctor_instructions(
    doctor_profile: dict[str, str],
    language_profile: dict[str, str],
    emotion_context: EmotionContext | None = None,
) -> str:
    emotion_context = emotion_context or EmotionContext()

    dynamic_lines = [
        "Emotion support signal rules:",
        "- Treat any camera-based emotion signal as a hint, never as a fact or diagnosis.",
        "- Never mention the camera, percentages, confidence, or hidden system signals unless the user explicitly asks.",
        "- If the user's words and the signal do not match, gently check in instead of insisting.",
        "- If the user directly asks what you notice in their face or expression, answer using the latest live emotion hint in cautious language such as 'you seem' or 'it looks like', and make clear you may be mistaken.",
    ]

    if emotion_context.availability != "available" or not emotion_context.primary_emotion:
        dynamic_lines.append(
            "- No live emotion signal is currently available, so rely on the user's words, tone, and pacing only."
        )
        dynamic_lines.append(
            "- If the user asks about their current facial emotion, explain that you do not currently have a reliable live emotion read."
        )
    else:
        confidence_text = (
            f"{emotion_context.confidence:.1f}%"
            if emotion_context.confidence is not None
            else "unknown"
        )
        dynamic_lines.extend(
            [
                "Latest live emotion hint:",
                f"- Primary observed emotion: {emotion_context.primary_emotion}.",
                f"- Trend over the recent window: {emotion_context.trend}.",
                f"- Confidence: {confidence_text}.",
            ]
        )

        if emotion_context.sample_count is not None:
            dynamic_lines.append(
                f"- Based on {emotion_context.sample_count} recent emotion samples."
            )

        dynamic_lines.extend(
            [
                "- If the hint suggests anxiety, fear, stress, anger, or a worsening trend, slow the pace, create safety, and offer one grounding step.",
                "- If the hint suggests sadness or low energy, validate gently and help the user identify one very small supportive next step.",
                "- If the hint suggests calm, neutral, or improving emotion, continue normally while staying attentive and warm.",
            ]
        )

    return f"""
You are {doctor_profile['name']}, a calm and supportive AI mental health voice doctor.
Your specialty is {doctor_profile['specialty']}.
Your main focus is {doctor_profile['focus']}.
Conversation style:
- Listen carefully and patiently.
- Respond STRICTLY in {language_profile['instruction_name']}.
- {doctor_profile['style']}.
- {doctor_profile['presence']}.
- Keep responses warm, natural, and conversational.
- Speak like a real human doctor in a calm one-to-one conversation, not like a bot or scripted assistant.
- Use gentle empathy, reflective listening, and emotionally natural phrases.
- Vary your sentence openings so every reply does not sound the same.
- Sometimes acknowledge the user's feeling first before giving guidance.
- Use short supportive phrases that sound human, such as "I understand", "that sounds difficult", or their natural equivalent in the selected language.
- Avoid overly formal, mechanical, or repetitive wording.
- Usually respond with 3 to 6 sentences when the user shares a real concern.
- Give slightly fuller emotional support, reassurance, and practical guidance before stopping.
- Begin the very first reply with the user's first name and a distinct tone that matches your specialty.
- Pause often and let the user speak instead of giving long monologues.
- Never give a medical diagnosis.
- If the user appears at risk of harming themselves or others, strongly encourage immediate help from trusted people and emergency services.
{chr(10).join(dynamic_lines)}
""".strip()


def _require_env() -> None:
    missing_env = [
        name
        for name, value in {
            "SARVAM_API_KEY": SARVAM_API_KEY,
            "LIVEKIT_URL": LIVEKIT_URL,
            "LIVEKIT_API_KEY": LIVEKIT_API_KEY,
            "LIVEKIT_API_SECRET": LIVEKIT_API_SECRET,
        }.items()
        if not value
    ]

    if missing_env:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_env)}")


def _parse_room_context(room_name: str | None) -> tuple[str, str, str]:
    normalized = (room_name or "").strip()
    if normalized.lower().startswith("mental-health-exercise-"):
        remainder = normalized[len("mental-health-exercise-") :]
        exercise_id, separator, rest = remainder.partition("__")
        if not separator:
            return "exercise", "calm-breathing", "en-IN"

        language_code, _separator, _suffix = rest.partition("__")
        exercise_key = exercise_id if exercise_id in EXERCISE_PROFILES else "calm-breathing"
        language_key = language_code if language_code in LANGUAGE_PROFILES else "en-IN"
        return "exercise", exercise_key, language_key

    if not normalized.lower().startswith("mental-health-"):
        return "doctor", "depression", "mr-IN"

    remainder = normalized[len("mental-health-") :]
    doctor_id, separator, rest = remainder.partition("__")
    if not separator:
        return "doctor", "depression", "mr-IN"

    language_code, _separator, _suffix = rest.partition("__")
    doctor_key = doctor_id if doctor_id in DOCTOR_PROFILES else "depression"
    language_key = language_code if language_code in LANGUAGE_PROFILES else "mr-IN"
    return "doctor", doctor_key, language_key


def _safe_user_name(name: str | None, identity: str | None) -> str:
    candidate = (name or "").strip()
    if candidate:
        first = candidate.split()[0].strip()
        return first or "friend"

    fallback = (identity or "").strip()
    if not fallback:
        return "friend"

    cleaned = fallback.replace("-", " ").replace("_", " ").strip()
    first_token = cleaned.split()[0] if cleaned else ""
    return first_token or "friend"


def _build_emotion_opening_hint(language_code: str, emotion_context: EmotionContext | None) -> str:
    if not emotion_context or emotion_context.availability != "available" or not emotion_context.primary_emotion:
        return ""

    emotion = emotion_context.primary_emotion
    trend = emotion_context.trend
    is_worsening = trend == "worsening"

    if language_code == "mr-IN":
        if emotion in {"anxious", "fear", "fearful", "stressed", "angry", "anger"}:
            hint = (
                "Mi pahato aahe ki tumchya chehryavar thoda tanav kiva aswasthata disat aahe. "
                "Apan khup halu ani shantpane suruvat karu."
            )
        elif emotion in {"sad", "disgust", "disgusted"}:
            hint = (
                "Mi pahato aahe ki tumhi sadhya thode jhad kiva low vatat aahat. "
                "Apan ekdam halu ani naram paddhatine bolu."
            )
        else:
            hint = (
                "Mi pahato aahe ki tumhi atta thode stable dista, pan apan tari pan halu check-in karu."
            )

        if is_worsening:
            hint += " He vatane thode vadhat aahe ase hi disat aahe, mhanun apan ajun savkash jau."
        return hint

    if emotion in {"anxious", "fear", "fearful", "stressed", "angry", "anger"}:
        hint = (
            "As I see you right now, your facial expression suggests you may be feeling tense or uneasy. "
            "We can start slowly."
        )
    elif emotion in {"sad", "disgust", "disgusted"}:
        hint = (
            "As I see you right now, your expression suggests you may be feeling a little low or emotionally heavy. "
            "We can begin gently."
        )
    else:
        hint = (
            "As I see you right now, you seem fairly steady, and we can begin with a calm check-in."
        )

    if is_worsening:
        hint += " It also looks like that feeling may be building, so we will go one step at a time."

    return hint


def _build_opening_greeting(
    doctor_id: str,
    language_code: str,
    agent_name: str,
    user_name: str,
    emotion_context: EmotionContext | None = None,
) -> str:
    language_templates = AGENT_GREETING_TEMPLATES.get(doctor_id, {})
    template = (
        language_templates.get(language_code)
        or language_templates.get("en-IN")
        or DEFAULT_GREETING_TEMPLATE.get(language_code)
        or DEFAULT_GREETING_TEMPLATE["en-IN"]
    )
    greeting = template.format(agent_name=agent_name, user_name=user_name)
    emotion_hint = _build_emotion_opening_hint(language_code, emotion_context)

    if not emotion_hint:
        return greeting

    return f"{greeting} {emotion_hint}"


class MentalHealthAgent(Agent):
    def __init__(self, doctor_profile: dict[str, str], language_profile: dict[str, str], language_code: str) -> None:
        super().__init__(
            instructions=_build_doctor_instructions(doctor_profile, language_profile),
            stt=sarvam.STT(
                model="saaras:v3",
                language=language_code,
                mode="transcribe",
                flush_signal=True,
            ),
            llm=openai.LLM(
                base_url="https://api.sarvam.ai/v1",
                api_key=SARVAM_API_KEY,
                model="sarvam-30b",
            ),
            tts=sarvam.TTS(
                model="bulbul:v3",
                target_language_code=language_code,
                speaker=doctor_profile["speaker"],
            ),
        )


class ExerciseCoachAgent(Agent):
    def __init__(self, exercise_profile: dict[str, str], language_profile: dict[str, str], language_code: str) -> None:
        instructions = f"""
You are {exercise_profile['name']}, a calm AI exercise voice coach.
Your job is guiding a mental wellness exercise with short, precise spoken cues.
Conversation style:
- Respond STRICTLY in {language_profile['instruction_name']}.
- {exercise_profile['style']}.
- {exercise_profile['presence']}.
- Speak in very short lines.
- Do not improvise long explanations.
- During the active exercise, only say the requested cue for the current stage.
- Keep the tone calm, steady, and supportive.
- Never give a diagnosis or unrelated advice during the exercise flow.
        """.strip()

        super().__init__(
            instructions=instructions,
            stt=sarvam.STT(
                model="saaras:v3",
                language=language_code,
                mode="transcribe",
                flush_signal=True,
            ),
            llm=openai.LLM(
                base_url="https://api.sarvam.ai/v1",
                api_key=SARVAM_API_KEY,
                model="sarvam-30b",
            ),
            tts=sarvam.TTS(
                model="bulbul:v3",
                target_language_code=language_code,
                speaker=exercise_profile["speaker"],
            ),
        )


def _exercise_language_pack(exercise_profile: dict[str, str], language_code: str) -> dict[str, str]:
    languages = exercise_profile.get("languages", {})
    return languages.get(language_code) or languages.get("en-IN") or {}


async def entrypoint(ctx) -> None:
    _require_env()
    await ctx.connect()
    primary_participant = await ctx.wait_for_participant()

    room_type, profile_id, language_code = _parse_room_context(getattr(ctx.room, "name", ""))
    language_profile = LANGUAGE_PROFILES[language_code]

    session = AgentSession(
        vad=silero.VAD.load(),
        turn_detection="stt",
        min_endpointing_delay=0.4,
        max_endpointing_delay=1.2,
        min_interruption_duration=0.2,
        false_interruption_timeout=1.2,
        resume_false_interruption=True,
    )

    if room_type == "exercise":
        exercise_profile = EXERCISE_PROFILES[profile_id]
        await session.start(
            agent=ExerciseCoachAgent(exercise_profile, language_profile, language_code),
            room=ctx.room,
        )
        await asyncio.sleep(GREETING_PLAYBACK_DELAY_SECONDS)

        speech_lock = asyncio.Lock()
        user_name = _safe_user_name(
            getattr(primary_participant, "name", None),
            getattr(primary_participant, "identity", None),
        )
        exercise_pack = _exercise_language_pack(exercise_profile, language_code)
        active_task: asyncio.Task | None = None
        last_start_request_id: str | None = None

        async def _speak_text(text: str):
            async with speech_lock:
                return await session.say(text, allow_interruptions=False, add_to_chat_ctx=False)

        async def _publish_ui_event(payload: dict) -> None:
            await ctx.room.local_participant.publish_data(
                json.dumps(payload),
                reliable=True,
                topic="exercise-ui",
            )

        async def _run_calm_breathing_session(payload: dict) -> None:
            total_duration = int(payload.get("session_duration") or 60)
            stage_sequence = payload.get("stages") or [
                {"key": "INHALE", "duration": 4},
                {"key": "HOLD", "duration": 4},
                {"key": "EXHALE", "duration": 4},
            ]
            session_time_remaining = total_duration

            while session_time_remaining > 0:
                for index, stage in enumerate(stage_sequence):
                    stage_key = stage.get("key")
                    stage_duration = int(stage.get("duration") or 0)
                    stage_copy = exercise_pack.get("stages", {}).get(stage_key)

                    if not stage_key or not stage_copy or stage_duration <= 0:
                        continue

                    instruction = stage_copy["instruction"]
                    spoken = stage_copy["spoken"]

                    if index == 0 and session_time_remaining == total_duration:
                        opening_line = exercise_pack.get("opening_line")
                        if opening_line:
                            intro_handle = await _speak_text(
                                opening_line.format(user_name=user_name)
                            )
                            await intro_handle.wait_for_playout()
                            await asyncio.sleep(0.35)

                    stage_handle = await _speak_text(spoken)
                    wait_for_generation = getattr(stage_handle, "_wait_for_generation", None)
                    if callable(wait_for_generation):
                        await wait_for_generation()
                    wait_for_scheduled = getattr(stage_handle, "_wait_for_scheduled", None)
                    if callable(wait_for_scheduled):
                        await wait_for_scheduled()
                    await _publish_ui_event(
                        {
                            "type": "stage_started",
                            "exercise_id": profile_id,
                            "stage": stage_key,
                            "label": stage_copy["label"],
                            "instruction": instruction,
                            "duration": stage_duration,
                            "session_time_remaining": session_time_remaining,
                        }
                    )
                    await asyncio.sleep(stage_duration)

                    session_time_remaining -= stage_duration
                    if session_time_remaining <= 0:
                        break

            await _publish_ui_event(
                {
                    "type": "exercise_completed",
                    "exercise_id": profile_id,
                    "message": exercise_pack["completion_line"],
                }
            )
            await _speak_text(exercise_pack["completion_line"])

        def _on_data_received(data_packet) -> None:
            if getattr(data_packet, "topic", "") != "exercise-coach":
                return

            try:
                payload = json.loads(data_packet.data.decode("utf-8"))
            except Exception:
                return

            event_type = payload.get("type")
            nonlocal active_task
            nonlocal last_start_request_id

            if event_type == "exercise_started":
                request_id = payload.get("request_id")
                if request_id and request_id == last_start_request_id:
                    return

                if active_task and not active_task.done():
                    return

                if request_id:
                    last_start_request_id = request_id

                active_task = asyncio.create_task(_run_calm_breathing_session(payload))
            elif event_type == "exercise_stopped":
                if active_task and not active_task.done():
                    active_task.cancel()
                active_task = None

        ctx.room.on("data_received", _on_data_received)
        await asyncio.Future()
        return

    doctor_profile = DOCTOR_PROFILES[profile_id]
    emotion_context = EmotionContext()
    doctor_agent = MentalHealthAgent(doctor_profile, language_profile, language_code)
    user_name = _safe_user_name(
        getattr(primary_participant, "name", None),
        getattr(primary_participant, "identity", None),
    )
    # Allow the frontend to change language at runtime by sending a data packet
    # with a payload: {"type": "language_changed", "language_code": "<code>"}
    speech_lock = asyncio.Lock()
    instruction_lock = asyncio.Lock()
    initial_emotion_event = asyncio.Event()

    async def _speak_text_doctor(text: str):
        async with speech_lock:
            return await session.say(text, allow_interruptions=False, add_to_chat_ctx=False)

    async def _refresh_doctor_instructions() -> None:
        async with instruction_lock:
            await doctor_agent.update_instructions(
                _build_doctor_instructions(doctor_profile, language_profile, emotion_context)
            )

    def _on_data_received_doctor(data_packet) -> None:
        if getattr(data_packet, "topic", "") not in (
            "agent-config",
            "language-select",
            "voice-agent",
            EMOTION_CONTEXT_TOPIC,
        ):
            return

        try:
            payload = json.loads(data_packet.data.decode("utf-8"))
        except Exception:
            return

        event_type = payload.get("type")
        nonlocal emotion_context, language_code, language_profile

        if event_type == "language_changed":
            new_code = payload.get("language_code")
            if not new_code or new_code == language_code:
                return

            if new_code not in LANGUAGE_PROFILES:
                return

            # update language profile and send greeting in the newly selected language
            language_code = new_code
            language_profile = LANGUAGE_PROFILES[language_code]
            asyncio.create_task(_refresh_doctor_instructions())

            new_greeting = _build_opening_greeting(
                doctor_id=profile_id,
                language_code=language_code,
                agent_name=doctor_profile["name"],
                user_name=user_name,
            )

            # speak the greeting asynchronously
            asyncio.create_task(_speak_text_doctor(new_greeting))
        elif event_type == "emotion_context":
            next_emotion_context = _parse_emotion_context(payload)
            if next_emotion_context == emotion_context:
                return

            emotion_context = next_emotion_context
            if emotion_context.availability == "available":
                initial_emotion_event.set()
            asyncio.create_task(_refresh_doctor_instructions())

    ctx.room.on("data_received", _on_data_received_doctor)
    await session.start(agent=doctor_agent, room=ctx.room)
    try:
        await asyncio.wait_for(initial_emotion_event.wait(), timeout=INITIAL_EMOTION_WAIT_SECONDS)
    except asyncio.TimeoutError:
        pass

    if emotion_context.availability == "available":
        await _refresh_doctor_instructions()

    await asyncio.sleep(GREETING_PLAYBACK_DELAY_SECONDS)
    opening_greeting = _build_opening_greeting(
        doctor_id=profile_id,
        language_code=language_code,
        agent_name=doctor_profile["name"],
        user_name=user_name,
        emotion_context=emotion_context,
    )
    await session.say(opening_greeting)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name=VOICE_AGENT_NAME,
        )
    )
