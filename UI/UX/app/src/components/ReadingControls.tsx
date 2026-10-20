import * as Switch from "@radix-ui/react-switch";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import { useSettings } from "../context/settingsState";
export function ReadingControls() {
  const { textSize, setTextSize, highContrast, setHighContrast } = useSettings();
  return <div className="reading-controls">
    <section><h2 id="text-size-heading">Text size</h2><p id="text-size-description" className="metadata">Choose the size that is easiest to read. The setting applies throughout the site.</p>
      <ToggleGroup.Root type="single" value={textSize} onValueChange={v => { if (v === "md" || v === "lg" || v === "xl") setTextSize(v); }} aria-labelledby="text-size-heading" aria-describedby="text-size-description" className="size-options">
        <ToggleGroup.Item value="md">Default</ToggleGroup.Item><ToggleGroup.Item value="lg">Large</ToggleGroup.Item><ToggleGroup.Item value="xl">Extra large</ToggleGroup.Item>
      </ToggleGroup.Root>
    </section>
    <section className="contrast-setting"><div><h2 id="contrast-heading">High contrast</h2><p id="contrast-description" className="metadata">Use stronger contrast between text, controls, and the background.</p></div>
      <div className="switch-target"><Switch.Root checked={highContrast} onCheckedChange={setHighContrast} aria-labelledby="contrast-heading" aria-describedby="contrast-description" className="contrast-switch"><Switch.Thumb className="contrast-thumb" /></Switch.Root></div>
    </section>
  </div>;
}
