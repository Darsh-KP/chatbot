import { Routes } from '@angular/router';
import { Chat } from './components/view/chat/chat';

export const routes: Routes = [
  { path: 'chats/new', component: Chat },
  { path: 'chats/:chat_id', component: Chat },

  { path: '**', redirectTo: 'chats/new' },
];
