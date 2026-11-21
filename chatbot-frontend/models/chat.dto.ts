/** Request body for BOTH POST /chats/new and POST /chats/{chat_id} */
export interface UserMessageRequest {
  user_message: string;
}

/** 201 response of POST /chats/new */
export interface NewChatResponse {
  chat_id: number;
  system_message: string;
}

/** 201 response of POST /chats/{chat_id} */
export interface MessageResponse {
  system_message: string;
}

/** Error body for 404 and 500 */
export interface ApiError {
  detail: string;
}

/** 422 error body: detail is an ARRAY, unlike 404/500 */
export interface ValidationErrorItem {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}
export interface ValidationError {
  detail: ValidationErrorItem[];
}