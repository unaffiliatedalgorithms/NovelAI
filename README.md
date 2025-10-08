<a id="readme-top"></a>
<!--
*** This readme was based off the best-readme-template from https://github.com/othneildrew/Best-README-Template
-->



<!-- PROJECT SHIELDS -->

[![GPL3 License][license-shield]][license-url]
[![Ethical Use Encouraged][ethics-shield]][ethics-url]



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#tested-with">Tested With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
    </li>
    <li><a href="#setup">Setup</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#ethics">Ethics</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This repository contains a recursive LLM based Novel generator. The framework is embedded in a Docker container and has currently been tested with an AMD GPU utilizing PyTorch and ROCm. This framework is an early work in progress. 
The core tenets in generating coherent text are a recursive questioning system on a text embedding vector space database. The database is populated by initial user provided text snippets and summaries which are repeated reworked and refined by asking structured questions and updating existing text snippets.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Tested With

Currently, I have only tested this framework with an AMD GPU. Some tweaks to the docker file would be needed for NVidia GPUs, but I suspect that it should be relatively straight forward (llamacpp compilation for Python would need to be replaced to allow for usage of ggfu type language models)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Quickstart (TL;DR)

1. Copy the base prompt from **[NarratorGPT](Prompts/Narrator/)** and fill in **Plot and Content** + **Style** at the end.
2. Paste the entire prompt into your LLM chat and submit. You’ll get the first DSL block.
3. To continue, send **""** (two quotation marks). Repeat to advance scenes until the epilogue.
4. Copy each **Author { ... }** DSL block into a single file, e.g. `my_novel.dsl`.
5. Export narrative + debug:
   ```bash
   python dsl2md.py my_novel.dsl

Initiating the DSL prompt framework fairly straightforward. Copy the text from the [NarratorGPT](Prompts/Narrator) text file (or copy one of the examples) and at the bottom of the prompt fill in "Plot and Content" and "Style". Paste your adapted prompt as is into your LLM's (e.g. ChatGPT or similar) web GUI chat dialogue and press enter. This will initiate the story generating style guidelines, the overarching plot and the first scene (among others). 
From this point on you can have the story auto-continue by entering "" into the prompt field.

This framework is very labor-intensive and takes a few minutes to complete one scene. For environmental (massive compute), ethical (harmful content) and legal (copyright) reasons, please use this framework wisely and responsibly.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Setup-->
## Setup

Top-level blocks per response:

- **HEADER_BLOCK** — global rules and parameters
- **UPDATE_BLOCK** — update current summary-tree ordinal in base-k
- **setting+arcmap** — fixed story drivers derived from the initial prompt
- **STATE_BLOCK** — memory registers at multiple scopes
- **SUMMARY_BLOCK** — backbone across scenes (k-ary tree context)
- **OUTLINE_BLOCK** — skeletal plan for the current leaf scene
- **SCENE_BLOCK** — the actual prose for the scene
- **DELTA_BLOCK** — register updates to apply next turn
- **end** — short self-review of rule adherence


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

After running the prompt a DSL code block with the response should be generated.

Wait a few minutes for a response to be generated and have the generator continue by entering "" into the prompt field (two quotation marks, that's it). Repeat this process until you reach the epilogue (after SPN^TD response), or however long you wish. You can also steer the generation by stating adaptations you want made. If you want to abort the DSL structure for any reason, you need to explicitly tell the llm to do this (eg. exit the DSL framework.)

**Exporting & parsing the DSL:** see [Post-Processing Tools(Python)](#post-processing)

### Prompt parameters (reference)

| Name | Type | What it controls | Typical values / notes |
|---|---|---|---|
| `Plot and content` | text | Rough outline, constraints, key setting traits | Free text |
| `Style` | text | Prose voice for `SCENE_BLOCK` | Free text |
| `Name` | text | Novel title | Free text |
| `USS` | int | Unique Story Symbols; injects diversity while anchoring plot | 3–20 |
| `LCA` | int range | Tokens per summary at each tree level | e.g., `90-120` |
| `SPN` | int | Summaries per node — the **k** in k-ary | 2–5 |
| `TD` | int | Total tree depth | 2–6 |
| `NL` | int range | Target scene length (tokens). NB often dominates length. | e.g., `500–800` |
| `IPR` | int | Min entries per register scope (`TD+1` registers) | e.g., `3–7` |
| `NB` | int range | Scenelets (beats) per scene | e.g., `12–18` |
| `CPB` | int | Max words per scenelet | e.g., `30–120` |
| `consequence` | word list | Tags for last scene to enforce rotation/variety | e.g., `{loss, gain, delay, interaction, reveal, transform}` |

_Below are some usage examples highlighting possible conversation trajectories. These are excerpts from memoryless chat windows initiated with the [NarratorGPT](Prompts/Narrator) prompts:_

* This is an example of a 64 scene (4-ary tree with depth 3) story, using Green Eggs and Ham by Dr. Zeuss as a guiding basis for style and story. Language style is strongly preserved throughout the whole narrative, but there is not much topic depth and the topics are restricted to a small initial set. However, the starting story arc, and the outline are followed to a degree. Managing drift vs lyrical freedom is quite challenging, but maybe someone else can find sweet spots to this balance. Remember, this is challenging because the complete narrative is essentially auto-generated. (The ChatGPT 5 thinking model was used here)
Check out the original dialogue if you want to check register, summary and related bookkeeping of the prompt. (Just beware there are over 500 full pages worth of text in the raw file)
  * [Narrative Text](Documents/EpicSam.scenes.md)
  * [Generator Prompt Text](Prompts/Narrator_EpicSam)
  * [Original ChatGPT dialogue + DSL structure](Documents/EpicSam_raw.md)



<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Troubleshooting -->
## Troubleshooting
Some ideas, but be aware that the framework is experimentary and highly volatile.

- **Parser skipped a block/crashes** — Ensure each `Author { ... }` block is complete and unbroken; remove non-DSL commentary; check dsl syntax.
- **Scenes too long/short** — Adjust `NB` (beats per scene) and `CPB` (max words per beat); `NL` is a soft target.
- **Drift or repetition** — Increase `IPR`, reduce `USS`, or add varied `consequence` tags to enforce rotation.
- **Context exhaustion** — Periodically summarize `STATE_BLOCK` and keep only the active path in the DSL.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- Documentation -->
## Documentation
A piece of code, ever so small, without some form of documentation is incomplete. Documentation still to come.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributing to this framework can currently best be done by testing it on various corporate scale LLM models and tracking what types of novels are more easily generated, and which are more types likely to fail. Feel free to modify the prompts to make them more lightweight, efficient or better in any other performance metric. Projects like this grow through deliberate application and reflected tinkering.

* In [THAL](https://github.com/unaffiliatedalgorithms/THAL) philosophy: These frameworks fulfill themselves by being exceeded


<!-- LICENSE -->
## License

[NarratorGPT](Prompts/Narrator) is intended as as a lightweight story generator and llm language space - dynamical system analysis tool. It is distributed under the GPL License to remain a publicly shared tool. See [`LICENSE`](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ETHICS -->
## Ethics

Distributed under the GPL License. See [`ETHICS`](ETHICS) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Web resources that were used in the context of this "project"

* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
* [GitHub Pages](https://pages.github.com)
* [Img Shields](https://shields.io)
* [ChatGPT][ChatGPT-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[ethics-shield]:https://img.shields.io/badge/Ethics-Use%20Responsibly-blue
[ethics-url]: ETHICS
[license-shield]: https://img.shields.io/badge/License-GPL3-green
[license-url]: LICENSE
[ChatGPT.com]: https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white
[ChatGPT-url]: https://chatgpt.com/
