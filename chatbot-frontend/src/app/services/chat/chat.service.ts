import {inject, Service} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, of} from 'rxjs';
import {AllChatsMetadataResponseDTO} from '../../dtos/chats/AllChatsMetadataResponseDTO';
import { AllChatMessagesResponseDTO } from '../../dtos/chats/AllChatMessagesResponseDTO';
import { MessageResponseDTO } from '../../dtos/chats/MessageResponseDTO';
import { UserMessageRequestDTO } from '../../dtos/chats/UserMessageRequestDTO';
import { NewChatSystemMessageResponseDTO } from '../../dtos/chats/NewChatSystemMessageResponseDTO';
import { SystemMessageResponseDTO } from '../../dtos/chats/SystemMessageResponseDTO';

@Service()
export class ChatService {
  private http = inject(HttpClient);
  private BASE_URL = 'http://127.0.0.1:8000/chats';

  getAllChatsMetadata(): Observable<AllChatsMetadataResponseDTO> {
    // return this.http.get<AllChatsMetadataResponseDTO>(this.BASE_URL);

    const mockData: AllChatsMetadataResponseDTO = {
      chats: [
        { chat_id: '101', title: 'Project Kickoff Discussion' },
        { chat_id: '102', title: 'Debugging Angular Signals' },
        { chat_id: '3861288806120089409', title: 'Weekend Hiking Plans' },
        { chat_id: '8125145216073083844', title: 'Code Review Notes' },
      ],
    };

    // Wraps the mock object inside an Observable stream
    return of(mockData);
  }

  getAllChatMessages(
    chat_id: string
  ): Observable<AllChatMessagesResponseDTO> {
    // return this.http.get<AllChatMessagesResponseDTO>(`${this.BASE_URL}/${chat_id}`);

    const nowInSeconds = Math.floor(Date.now() / 1000);

    // Dynamic mock dictionaries grouped by string chat_id keys
    const mockDb: Record<string, MessageResponseDTO[]> = {
      '101': [
        {
          role: 0,
          message:
            'Can you help me design a robust structure for a modern Angular service that connects to a REST API?',
          epoch_seconds: nowInSeconds - 7200,
        },
        {
          role: 1,
          message: `### Designing a Scalable Angular Service

To handle API requests professionally in Angular, you should leverage **Signals** alongside the standard \`HttpClient\`. Here is a structural blueprint:

1. **Keep it lean:** Your service should only handle data orchestration (fetching, mapping, and posting data).
2. **Encapsulate state:** Use Signals inside your service or map responses using \`rxResource\` directly inside your components.

#### Code Implementation Blueprint
\`\`\`typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DataService {
  private http = inject(HttpClient);
  private readonly API_URL = 'https://my-domain.com';

  // Always strongly type your Observable payload responses
  getItems(): Observable<ItemResponse[]> {
    return this.http.get<ItemResponse[]>(this.API_URL);
  }
}
\`\`\``,
          epoch_seconds: nowInSeconds - 7000,
        },
        {
          role: 0,
          message:
            'Excellent. What is the standard configuration pattern to make sure the app handles loading and fallback states beautifully?',
          epoch_seconds: nowInSeconds - 6500,
        },
        {
          role: 1,
          message: `### Managing Application View States

To handle states cleanly, you should track **three core pillars**:
* **Loading State:** Display visual skeleton loaders while active network background worker sync operations resolve.
* **Empty State:** Handle instances where the payload parses successfully but contains zero internal entries.
* **Error State:** Intercept and gracefully capture non-200 boundary alerts cleanly.

You can handle this directly within your UI component template using Angular's modern structural syntax:
\`\`\`html
@if (dataResource.isLoading()) {
  <app-loading-skeleton />
} @else if (dataResource.error()) {
  <app-error-banner [error]="dataResource.error()" />
} @else {
  <app-data-display-grid [items]="items()" />
}
\`\`\``,
          epoch_seconds: nowInSeconds - 6000,
        },
        {
          role: 0,
          message:
            'Perfect, that matches exactly what I needed. Thanks for compiling this breakdown!',
          epoch_seconds: nowInSeconds - 5500,
        },
      ],
      '102': [
        {
          role: 0,
          message: 'Why is my standard signal input returning undefined in the child component?',
          epoch_seconds: nowInSeconds - 3600,
        },
        {
          role: 1,
          message: `### Resolving Undefined Router Inputs

Make sure you added \`withComponentInputBinding()\` to your application router configuration! Otherwise, the router inputs won't bind to component elements dynamically.

#### Global Setup Check
Verify your configuration file maps out like this:
\`\`\`typescript
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding())
  ]
};
\`\`\``,
          epoch_seconds: nowInSeconds - 3500,
        },
        {
          role: 0,
          message: 'Ah! That fixed it instantly. Thank you!',
          epoch_seconds: nowInSeconds - 3400,
        },
        {
          role: 1,
          message: `Awesome! Glad it resolved the issue.

Here's a quick summary of what just happened behind the scenes:
* **The Route Parameter Parser** scanned the browser URL address window.
* **The Engine** matched the path string token properties natively.
* **The Reactive Pipeline** dynamically injected the text into your component input block.

Let me know if you run into any layout or alignment challenges with your view component blocks!`,
          epoch_seconds: nowInSeconds - 3300,
        },
      ],
      // Adding your 64-bit integer ID explicitly as a string key to demonstrate stability
      '3861288806120089409': [
        {
          role: 1,
          message: `### Production 64-Bit Lookup Success
This conversation string loaded without precision truncation or float rounding issues.`,
          epoch_seconds: nowInSeconds - 120,
        },
      ],
    };

    const defaultMessages: MessageResponseDTO[] = [
      {
        role: 1,
        message: `### Dynamic Workspace Init

Welcome to chat thread **#${chat_id}**!

* Standard contextual payload mappings initialized successfully.
* Markdown formatting subroutines active.

How can I help you build or refine your application today?`,
        epoch_seconds: nowInSeconds,
      },
    ];

    const responsePayload: AllChatMessagesResponseDTO = {
      messages: mockDb[chat_id] || defaultMessages,
    };

    return of(responsePayload);
  }

  postFirstChatMessage(
    userMessageRequestDTO: UserMessageRequestDTO
  ): Observable<NewChatSystemMessageResponseDTO> {
    return this.http.post<NewChatSystemMessageResponseDTO>(`${this.BASE_URL}/new`, userMessageRequestDTO);
  }

  postChatMessage(
    chat_id: string,
    userMessageRequestDTO: UserMessageRequestDTO
  ): Observable<SystemMessageResponseDTO>{
    return this.http.post<SystemMessageResponseDTO>(`${this.BASE_URL}/${chat_id}`, userMessageRequestDTO);
  }

  deleteChat(
    chat_id: string
  ): Observable<any> {
    return this.http.delete(`${this.BASE_URL}/${chat_id}`);
  }
}
