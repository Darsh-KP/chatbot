import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Chat } from './chat';

describe('Chat', () => {
  let component: Chat;
  let fixture: ComponentFixture<Chat>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Chat],
    }).compileComponents();

    fixture = TestBed.createComponent(Chat);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // some generated tests
  it('should switch the displayed conversation when a thread is selected', () => {
    fixture.detectChanges();

    const nativeElement: HTMLElement = fixture.nativeElement;
    const threadButtons = nativeElement.querySelectorAll<HTMLButtonElement>('.chat-thread');

    expect(threadButtons.length).toBe(5);
    expect(nativeElement.querySelector('main')?.textContent).toContain(
      'How do I configure a custom connection pool size',
    );

    // Choosing another thread updates the same message layout rather than replacing the chat view.
    threadButtons[1].click();
    fixture.detectChanges();

    expect(nativeElement.querySelector('main')?.textContent).toContain(
      'What is the usual way to build a REST API in Spring Boot?',
    );
    expect(threadButtons[1].getAttribute('aria-current')).toBe('page');
  });

  it('should toggle the page color scheme', () => {
    fixture.detectChanges();

    const nativeElement: HTMLElement = fixture.nativeElement;
    const layout = nativeElement.querySelector('.chat-layout');
    const themeButton = nativeElement.querySelector<HTMLButtonElement>(
      '[aria-label="Switch to light theme"]',
    );

    expect(layout?.classList.contains('light-theme')).toBe(false);

    themeButton?.click();
    fixture.detectChanges();

    expect(layout?.classList.contains('light-theme')).toBe(true);
    expect(
      nativeElement.querySelector('[aria-label="Switch to dark theme"]'),
    ).toBeTruthy();
  });
});
