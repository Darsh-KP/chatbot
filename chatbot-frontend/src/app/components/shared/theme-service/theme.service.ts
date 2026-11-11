import { Service, signal, effect } from '@angular/core';

@Service()
export class ThemeService {
  // Key for local storage
  private readonly STORAGE_KEY = 'is-dark-mode';

  // Store the current theme
  readonly isDarkMode = signal<boolean>(this.getInitialThemePreference());

  // Automatically call updateRenderedTheme if the isDarkMode signal changes
  constructor() {
    effect(() => {
      this.updateRenderedTheme(this.isDarkMode());
    });
  }

  // Components can call this method to flip the theme
  toggleTheme(): void {
    this.isDarkMode.update((dark) => !dark);
  }

  // Read the initial theme preference form local storage
  private getInitialThemePreference(): boolean {
    // Check if localStorage exists
    if (typeof window !== 'undefined' && window.localStorage) {
      // Get the current saved theme value
      const saved = localStorage.getItem(this.STORAGE_KEY);

      // Default true (dark theme)
      return saved !== null ? saved === 'true' : true;
    }

    // Default true (dark theme)
    return true;
  }

  // Update the class on the <body> tag
  // (Angular Material, by default, defines it on the <body> tag)
  private updateRenderedTheme(isDark: boolean): void {
    // Check if the reference to current document is not undefined
    if (typeof document !== 'undefined') {
      // Get the <body> tag
      const target = document.body;

      // Check if it is dark theme
      if (isDark) {
        // Set the class of <body> tag to dark-theme
        target.classList.remove('light-theme');
        target.classList.add('dark-theme');
      } else {
        // Set the class of <body> tag to light-theme
        target.classList.remove('dark-theme');
        target.classList.add('light-theme');
      }

      // Update the value in local storage
      localStorage.setItem(this.STORAGE_KEY, String(isDark));
    }
  }
}
