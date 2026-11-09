import { Component, inject, signal } from '@angular/core';
import { MatMiniFabButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { ThemeService } from '../../shared/theme-service/theme.service';

// this interface would be a DTO (some properties might not be necessary)
interface ChatThread {
  id: string;
  title: string;
  question: string;
  answerIntro: string;
  answerCodeLabel?: string;
  answerAfterCode?: string;
  answerCode?: string;
  answerDetail?: string;
}

// Keep the initial conversation's original copy while giving the sidebar local sample threads.
// hardcoded chat threads for visualization -> this would be replaced with a call to the backend
const THREADS: ChatThread[] = [
  {
    id: 'hikari-pool',
    title: 'Configure HikariCP pool size',
    question: 'How do I configure a custom connection pool size in Spring Boot using HikariCP?',
    answerIntro: 'You can configure it directly in your ',
    answerCodeLabel: 'application.properties',
    answerAfterCode: ' file:',
    answerCode: 'spring.datasource.hikari.maximum-pool-size=20',
    answerDetail:
      'This sets the maximum number of simultaneous connections allowed in the pool. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
  },
  {
    id: 'rest-api',
    title: 'Build a REST API',
    question: 'What is the usual way to build a REST API in Spring Boot?',
    answerIntro:
      'Create a controller with @RestController, map routes with request-mapping annotations, and delegate business logic to a service.',
  },
  {
    id: 'dependency-injection',
    title: 'Dependency injection',
    question: 'How does dependency injection work in Spring?',
    answerIntro:
      'Spring creates and manages application objects as beans, then injects their dependencies through constructors or other supported injection points.',
  },
  {
    id: 'spring-profiles',
    title: 'Use Spring profiles',
    question: 'How can I use different Spring profiles for development and production?',
    answerIntro:
      'Put environment-specific settings in files such as application-dev.properties and application-prod.properties, then activate the profile you need.',
  },
];

@Component({
  imports: [MatMiniFabButton, MatIcon, CdkTextareaAutosize],
  selector: 'app-chat',
  styleUrl: './chat.css',
  templateUrl: './chat.html',
})
export class Chat {
  // Inject the theme service and read the current theme
  themeService = inject(ThemeService);
  protected readonly isDarkTheme = this.themeService.isDarkMode;

  protected readonly threads = THREADS;
  protected readonly selectedThread = signal(THREADS[0]);

  protected selectThread(thread: ChatThread): void {
    this.selectedThread.set(thread);
  }
}
