import { Component, input } from '@angular/core';
import { MessageSenderType } from './MessageSenderType';
import { MarkdownComponent } from 'ngx-markdown';

@Component({
  imports: [MarkdownComponent],
  selector: 'app-chat-message',
  styleUrl: './chat-message.css',
  templateUrl: './chat-message.html',
})
export class ChatMessage {
  // Get inputs for message type and content
  senderType = input.required<MessageSenderType>();
  content = input.required<string>();
}
