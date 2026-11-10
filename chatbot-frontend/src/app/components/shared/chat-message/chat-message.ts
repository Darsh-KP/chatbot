import { Component, input } from '@angular/core';
import { MessageSenderType, transformSender } from './MessageSenderType';
import { MarkdownComponent } from 'ngx-markdown';

@Component({
  imports: [MarkdownComponent],
  selector: 'app-chat-message',
  styleUrl: './chat-message.css',
  templateUrl: './chat-message.html',
  host: {
    style: 'display: contents;',
  },
})
export class ChatMessage {
  // Get inputs for message type and content
  senderType = input.required<MessageSenderType, number | string | MessageSenderType>({
    transform: transformSender
  });
  content = input.required<string>();
}
