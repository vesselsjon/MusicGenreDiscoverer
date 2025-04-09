import { Component, Renderer2 } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: false,
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
  //#region Inputs, Outputs, ViewChilds
  //#endregion Inputs, Outputs, ViewChilds

  //#region Public Variables
  //#endregion Public Variables

  //#region Private Variables
  //#endregion Private Variables

  //#region Properties
  //#endregion Properties

  //#region Constructor and Angular Life Cycle
  constructor(private renderer: Renderer2) { }

  public ngOnInit(): void {
    // Set the initial theme based on localStorage or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.renderer.setAttribute(document.body, 'data-theme', savedTheme);
  }
  //#endregion Constructor and Angular Life Cycle

  //#region Event Handlers
  //#endregion Event Handlers

  //#region Public Methods
  public ToggleTheme(): void {
    const currentTheme = localStorage.getItem('theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    // Set the theme in the body element
    this.renderer.setAttribute(document.body, 'data-theme', newTheme);
    // Store the theme preference in localStorage
    localStorage.setItem('theme', newTheme);
  }
  //#endregion Public Methods

  //#region Private Methods
  //#endregion Private Methods
}
