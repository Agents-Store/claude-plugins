# Community shadcn Registries

30+ free registries that provide UI components, blocks, and templates compatible with shadcn/ui v4.

**URL convention**: Most registries follow `https://domain.com/r/{name}`. The easiest way to verify a URL is to install one component: `npx shadcn@latest add @registry/component` — the CLI auto-resolves known registries.

**Full directory**: https://ui.shadcn.com/docs/directory (170+ registries total, including auth, infrastructure, and paid registries not listed here)

---

## Animation & Motion

| Registry | URL | Description |
|----------|-----|-------------|
| @magicui | `https://magicui.design/r` | 50+ animated components — shimmer buttons, animated beams, globe, particles, meteors, marquee |
| @aceternity | `https://ui.aceternity.com/r` | Motion-heavy effects — parallax scroll, moving border, spotlight, aurora background, 3D cards |
| @animate-ui | `https://animate-ui.com/r` | Smooth transition components — animated accordion, fade-in, slide, reveal effects |
| @cult-ui | `https://www.cult-ui.com/r` | Creative animations — flyout menus, hover reveals, morphing shapes |
| @motion-primitives | `https://motion-primitives.com/r` | Motion building blocks — transition, animate-presence, gesture primitives |
| @chamaac | `https://chamaac.com/r` | Animation effects — glow, ripple, magnetic cursor, tilt effects |

## Extended UI Components

| Registry | URL | Description |
|----------|-----|-------------|
| @originui | `https://originui.com/r` | 100+ styled component variants — buttons, inputs, cards with extra design options |
| @diceui | `https://www.diceui.com/r` | Interactive components — combobox, tags input, editable text, kanban board |
| @basecn | `https://basecn.dev/r` | Base component extensions — enhanced select, multi-select, command palette |
| @8bitcn | `https://www.8bitcn.com/r` | Retro pixel-style UI components — 8-bit buttons, pixel cards, retro badges |
| @boldkit | `https://boldkit.dev/r` | Bold design system — distinctive buttons, cards, layouts |
| @8starlabs-ui | `https://ui.8starlabs.com/r` | Additional UI components and variants |
| @cardcn | `https://cardcn.dev/r` | Card-focused components — pricing cards, profile cards, feature cards, stat cards |
| @unlumen-ui | `https://ui.unlumen.com/r` | Minimalist UI components |

## Blocks & Sections

| Registry | URL | Description |
|----------|-----|-------------|
| @bundui | `https://bundui.io/r` | Landing page blocks — hero sections, feature grids, pricing tables, testimonials |
| @blocks-so | `https://blocks.so/r` | Marketing blocks — CTA sections, navigation, footers, content sections |
| @efferd | `https://efferd.com/r` | Pre-built page sections — headers, footers, feature sections |
| @doras-ui | `https://ui.doras.to/r` | Dashboard and application blocks |
| @creative-tim | `https://www.creative-tim.com/ui/r` | Professional UI blocks — admin dashboards, landing pages, e-commerce sections |

## E-Commerce

| Registry | URL | Description |
|----------|-----|-------------|
| @commerce-ui | `https://commerce-ui.com/r` | E-commerce components — product cards, shopping cart, checkout flow, reviews, wishlists |

## AI Components

| Registry | URL | Description |
|----------|-----|-------------|
| @ai-elements | `https://ai-sdk.dev/elements/r` | Vercel AI SDK UI elements — chat interfaces, streaming response displays |
| @assistant-ui | `https://www.assistant-ui.com/r` | AI assistant UIs — chat bubbles, thread views, suggested prompts, tool call displays |
| @tool-ui | `https://www.tool-ui.com/r` | Tool/function call UIs for AI agents — tool result cards, execution status |
| @ai-blocks | `https://webllm.org/blocks/r` | WebLLM blocks — browser-based LLM interfaces, local inference UIs |

## File Upload

| Registry | URL | Description |
|----------|-----|-------------|
| @better-upload | `https://better-upload.com/r` | Upload components — drag-and-drop zones, progress indicators, file previews |

## Other

| Registry | URL | Description |
|----------|-----|-------------|
| @arc | `https://witharc.co/components/r` | Design system components |
| @abui | `https://abui.io/r` | Additional UI component library |
| @aevr | `https://ui.aevr.space/r` | UI component variants |
| @einui | `https://ui.eindev.ir/r` | Extended UI components |
| @billingsdk | `https://billingsdk.com/r` | Billing and payment form components — subscription management, plan selectors |

---

## components.json Configuration

To add all registries to `components.json` for MCP search:

```json
{
  "registries": {
    "@magicui": "https://magicui.design/r/{name}",
    "@aceternity": "https://ui.aceternity.com/r/{name}",
    "@animate-ui": "https://animate-ui.com/r/{name}",
    "@originui": "https://originui.com/r/{name}",
    "@cult-ui": "https://www.cult-ui.com/r/{name}",
    "@motion-primitives": "https://motion-primitives.com/r/{name}",
    "@bundui": "https://bundui.io/r/{name}",
    "@blocks-so": "https://blocks.so/r/{name}",
    "@efferd": "https://efferd.com/r/{name}",
    "@doras-ui": "https://ui.doras.to/r/{name}",
    "@8bitcn": "https://www.8bitcn.com/r/{name}",
    "@boldkit": "https://boldkit.dev/r/{name}",
    "@basecn": "https://basecn.dev/r/{name}",
    "@diceui": "https://www.diceui.com/r/{name}",
    "@cardcn": "https://cardcn.dev/r/{name}",
    "@chamaac": "https://chamaac.com/r/{name}",
    "@commerce-ui": "https://commerce-ui.com/r/{name}",
    "@ai-elements": "https://ai-sdk.dev/elements/r/{name}",
    "@assistant-ui": "https://www.assistant-ui.com/r/{name}",
    "@tool-ui": "https://www.tool-ui.com/r/{name}",
    "@creative-tim": "https://www.creative-tim.com/ui/r/{name}",
    "@better-upload": "https://better-upload.com/r/{name}",
    "@8starlabs-ui": "https://ui.8starlabs.com/r/{name}",
    "@unlumen-ui": "https://ui.unlumen.com/r/{name}",
    "@arc": "https://witharc.co/components/r/{name}",
    "@abui": "https://abui.io/r/{name}",
    "@aevr": "https://ui.aevr.space/r/{name}",
    "@ai-blocks": "https://webllm.org/blocks/r/{name}",
    "@einui": "https://ui.eindev.ir/r/{name}",
    "@billingsdk": "https://billingsdk.com/r/{name}"
  }
}
```

Merge this with existing registries in `components.json` — do not replace the entire file.
