import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatMiniFabButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { ThemeService } from '../../shared/theme-service/theme.service';
import { GifContainer } from '../../shared/gif-container/gif-container';
import { ResponsePhase } from '../../shared/gif-container/ResponsePhase';
import {ChatService} from '../../../services/chat/chat.service';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { MessageResponseDTO } from '../../../dtos/chats/MessageResponseDTO';
import { ChatMessage } from '../../shared/chat-message/chat-message';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';

@Component({
  imports: [
    MatMiniFabButton,
    MatIcon,
    CdkTextareaAutosize,
    GifContainer,
    RouterLink,
    RouterLinkActive,
    ChatMessage,
    MatProgressSpinner,
    ReactiveFormsModule,
  ],
  selector: 'app-chat',
  styleUrl: './chat.css',
  templateUrl: './chat.html',
})
export class Chat {
  // Inject required dependencies
  chatService = inject(ChatService);
  private readonly router = inject(Router);

  // Inject the theme service and read the current theme
  themeService = inject(ThemeService);
  protected readonly isDarkTheme = this.themeService.isDarkMode;

  // Track the current chat
  chat_id = input<string | undefined>();

  // Hold your message state
  messages = signal<MessageResponseDTO[]>([]);

  // To track if we are waiting for a system response
  readonly loading = signal<boolean>(false);

  constructor() {
    // Automatically re-run this logic whenever the URL link shifts!
    effect(() => {
      const currentId = this.chat_id();

      console.log('current chat: ' + currentId);

      if (currentId && currentId !== 'new') {
        // State A: We have a real chat ID -> Fetch history
        this.chatService.getAllChatMessages(currentId).subscribe((response) => {
          this.messages.set(response.messages);
        });
      } else {
        // State B: We are on 'chats/new' -> Clear out the chat bubble window
        this.messages.set([]);
      }
    });
  }

  //Default animation is greeting
  protected gifPhase: ResponsePhase = 'greeting';

  // Get all the chats' metadata
  readonly chatsMetadata = toSignal(this.chatService.getAllChatsMetadata(), {
    initialValue: null,
  });

  // Stores all the deleted chatIds for non-connected service
  private readonly deletedChatIds = signal<ReadonlySet<string>>(new Set());

  // only displays the VISIBLE chat metadata
  readonly visibleChatsMetadata = computed(() => {
    const metadata = this.chatsMetadata();
    if (!metadata) {
      return null;
    }

    const deletedChatIds = this.deletedChatIds();
    return {
      ...metadata,
      chats: metadata.chats.filter((chat) => !deletedChatIds.has(chat.chat_id)),
    };
  });

  // Stores all the currently DELETING chatIds
  readonly deletingChatIds = signal<ReadonlySet<string>>(new Set());

  // placeholder instead of a snackbar/toast for error handling
  readonly deleteError = signal<string | null>(null);

  // function will delete a chat by its id
  deleteChat(chatId: string): void {
    if (this.deletingChatIds().has(chatId)) {
      return;
    }

    this.deleteError.set(null);
    this.deletingChatIds.update((ids) => new Set(ids).add(chatId));

    // calls the service and deletes it from DB
    this.chatService
      .deleteChat(chatId)
      .pipe(
        finalize(() => {
          this.deletingChatIds.update((ids) => {
            const nextIds = new Set(ids);
            nextIds.delete(chatId);
            return nextIds;
          });
        }),
      )
      .subscribe({
        next: () => {
          this.deletedChatIds.update((ids) => new Set(ids).add(chatId));

          // navigate to new if deleting current chat
          if (this.chat_id() === chatId) {
            void this.router.navigate(['/chats', 'new']);
          }
        },
        error: () => {
          this.deleteError.set('Unable to delete chat. Please try again.');
        },
      });
  }

  // Get the user input control
  readonly userInputControl = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required],
  });

  // Handle sending user message
  submitUserMessage(): void {
    const userMessage = this.userInputControl.value.trim();

    if (!userMessage) {
      return;
    }

    this.loading.set(true);

    // Add sent message to displayed chat
    this.messages.update((prev) => [
      ...prev,
      {
        role: 0,
        message: userMessage,
        epoch_seconds: Math.floor(Date.now() / 1000),
        seq_num: prev.length + 1,
      },
    ]);
    this.userInputControl.reset();

    const chatId = this.chat_id();

    if (chatId) {
      this.chatService
        .postChatMessage(chatId, {
          user_message: userMessage,
        })
        .subscribe({
          next: (response) => {
            // Add response to displayed chat
            this.messages.update((prev) => [
              ...prev,
              {
                role: 1,
                message: response.system_message,
                epoch_seconds: response.epoch_seconds,
                seq_num: response.seq_num,
              },
            ]);
            this.loading.set(false);
          },

          error: (error) => {
            console.log(error);
            this.loading.set(false);
          },
        });
    } else {
      this.chatService
        .postFirstChatMessage({
          user_message: userMessage,
        })
        .subscribe({
          next: (response) => {
            // Add response to displayed chat
            this.loading.set(false);
            void this.router.navigate(['/chats', response.chat_id]);
          },

          error: (error) => {
            console.log(error);
            this.loading.set(false);
          },
        });
    }
  }
}
