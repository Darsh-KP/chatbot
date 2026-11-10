import { Component, effect, inject, input, signal } from '@angular/core';
import { MatMiniFabButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { ThemeService } from '../../shared/theme-service/theme.service';
import { GifContainer } from '../../shared/gif-container/gif-container';
import { ResponsePhase } from '../../shared/gif-container/ResponsePhase';
import {ChatService} from '../../../services/chat/chat.service';
import {AsyncPipe} from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { MessageResponseDTO } from '../../../dtos/chats/MessageResponseDTO';
import { ChatMessage } from '../../shared/chat-message/chat-message';
import { MatProgressSpinner } from '@angular/material/progress-spinner';

@Component({
  imports: [
    MatMiniFabButton,
    MatIcon,
    CdkTextareaAutosize,
    GifContainer,
    AsyncPipe,
    RouterLink,
    RouterLinkActive,
    ChatMessage,
    MatProgressSpinner,
  ],
  selector: 'app-chat',
  styleUrl: './chat.css',
  templateUrl: './chat.html',
})
export class Chat {
  // Inject required dependencies
  chatService = inject(ChatService);

  // Inject the theme service and read the current theme
  themeService = inject(ThemeService);
  protected readonly isDarkTheme = this.themeService.isDarkMode;

  // Track the current chat
  chat_id = input<string | undefined>();

  // Hold your message state
  messages = signal<MessageResponseDTO[]>([]);

  constructor() {
    // Automatically re-run this logic whenever the URL link shifts!
    effect(() => {
      const currentId = this.chat_id();

      console.log(currentId);

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
  chatsMetadata$ = this.chatService.getAllChatsMetadata();
}
