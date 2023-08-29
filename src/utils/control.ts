import type { ControlPosition, IControl, Map } from 'maplibre-gl'

/**
 * https://maplibre.org/maplibre-gl-js-docs/api/markers/#icontrol
 */
export class DivControl implements IControl {
  public container?: HTMLDivElement

  constructor(
    private options: {
      id: string
    }
  ) {}

  onAdd() {
    this.container = document.createElement('div')
    this.container.className = 'px-3 py-1'
    this.container.id = this.options.id
    return this.container
  }

  onRemove() {
    this.container?.parentNode?.removeChild(this.container)
    this.container = undefined
  }
}

export type ThemeDefinition =
{
    id: string
    label: string
}

export type ThemeSwitcherOptions =
{
    defaultStyle?: string
    eventListeners?: ThemeSwitcherEvents
}

type ThemeSwitcherEvents =
{
    onOpen?: (event: MouseEvent) => boolean
    onSelect?: (event: MouseEvent) => boolean
    onChange?: (event: MouseEvent, style: string | undefined) => boolean
}

export class ThemeControl implements IControl {
  private static readonly DEFAULT_STYLE = "light";
  private static readonly DEFAULT_STYLES: ThemeDefinition[] = [
    {
      "id": "classic",
      "label": "Classic"
    },
    {
      "id": "light",
      "label": "Light"
    },
    {
      "id": "dark",
      "label": "Dark"
    }
  ];

  private controlContainer: HTMLElement | undefined;
  private events?: ThemeSwitcherEvents;
  private map?: Map;
  private themeContainer: HTMLElement | undefined;
  private styleButton: HTMLButtonElement | undefined;
  private styles: ThemeDefinition[];
  private defaultStyle: string;

  constructor(styles?: ThemeDefinition[], options?: ThemeSwitcherOptions | string) {
    this.styles = styles ?? ThemeControl.DEFAULT_STYLES;
    const defaultStyle = typeof(options) === "string" ? options : options ? options.defaultStyle : undefined;
    this.defaultStyle = defaultStyle || ThemeControl.DEFAULT_STYLE;
    this.onDocumentClick = this.onDocumentClick.bind(this);
    this.events = typeof(options) !== "string" && options ? options.eventListeners : undefined;
  }

  public getDefaultPosition(): ControlPosition {
    const defaultPosition = "top-right";
    return defaultPosition;
  }

  public onAdd(map: Map): HTMLElement {
    this.map = map;
    this.controlContainer = document.createElement("div");
    this.controlContainer.classList.add("maplibregl-ctrl");
    this.controlContainer.classList.add("maplibregl-ctrl-group");
    this.themeContainer = document.createElement("div");
    this.styleButton = document.createElement("button");
    this.styleButton.type = "button";
    this.themeContainer.classList.add("theme-list");
    for (const style of this.styles) {
        const styleElement = document.createElement("button");
        styleElement.type = "button";
        styleElement.innerText = style.label;
        styleElement.classList.add(style.label.replace(/[^a-z0-9-]/gi, '_'));
        styleElement.dataset.id = style.id;
        styleElement.addEventListener("click", event => {
          const srcElement = event.srcElement as HTMLButtonElement;
          this.closeModal();
          if (srcElement.classList.contains("active")) {
            return;
          }
          if (this.events && this.events.onOpen && this.events.onOpen(event)) {
            return;
          }
          const styleId = srcElement.dataset.id;
          if (this.map?.loaded()) {
            this.map?.getStyle().layers
              .filter((layer) => this.styles.map((style) => style.id).includes(layer.id))
              .forEach((layer) => {
                this.map?.setLayoutProperty(
                  layer.id,
                  'visibility',
                  layer.id === styleId ? 'visible' : 'none'
                )
              })
          }
          const elms = this.themeContainer!.getElementsByClassName("active");
          while (elms[0]) {
              elms[0].classList.remove("active");
          }
          srcElement.classList.add("active");
          if (this.events && this.events.onChange && this.events.onChange(event, styleId)) {
            return;
          }
        });
        if (style.id === this.defaultStyle) {
          styleElement.classList.add("active");
        }
        this.themeContainer.appendChild(styleElement);
    }
    this.styleButton.classList.add("maplibregl-ctrl-icon");
    this.styleButton.classList.add("theme-switcher");
    this.styleButton.addEventListener("click", event => {
      if (this.events && this.events.onSelect && this.events.onSelect(event)) {
        return;
      }
      this.openModal();
    });

    document.addEventListener("click", this.onDocumentClick);

    this.controlContainer.appendChild(this.styleButton);
    this.controlContainer.appendChild(this.themeContainer);
    return this.controlContainer;
  }

  public onRemove(): void {
    if (!this.controlContainer || !this.controlContainer.parentNode || !this.map || !this.styleButton) {
      return;
    }
    this.styleButton.removeEventListener("click", this.onDocumentClick);
    this.controlContainer.parentNode.removeChild(this.controlContainer);
    document.removeEventListener("click", this.onDocumentClick);
    this.map = undefined;
  }

  private closeModal(): void {
    if (this.themeContainer && this.styleButton) {
      this.themeContainer.style.display = "none";
      this.styleButton.style.display = "block";
    }
  }

  private openModal(): void {
    if (this.themeContainer && this.styleButton) {
      this.themeContainer.style.display = "block";
      this.styleButton.style.display = "none";
    }
  }

  private onDocumentClick(event: MouseEvent): void {
    if (this.controlContainer && !this.controlContainer.contains(event.target as Element)) {
      this.closeModal();
    }
  }
}