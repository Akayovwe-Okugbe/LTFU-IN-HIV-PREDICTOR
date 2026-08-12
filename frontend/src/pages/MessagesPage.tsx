import {
  ArrowLeft,
  Inbox,
  Mail,
  MailOpen,
  MessageSquareText,
  MoreHorizontal,
  PenLine,
  Search,
  Send,
  Trash2,
  X,
} from 'lucide-react';

import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react';

import {
  PageHeader,
} from '../components/UI';

import {
  api,
} from '../lib/api';

import type {
  MessageItem,
  MessageRecipient,
  SentMessageItem,
} from '../lib/types';


// =====================================================
// MESSAGE FOLDERS
// =====================================================

type Folder =
  | 'inbox'
  | 'unread'
  | 'sent';


// =====================================================
// DATE FORMATTING
// =====================================================

function formatMessageDate(
  value: string,
): string {
  const date =
    new Date(value);

  const today =
    new Date();

  const isToday =
    date.toDateString()
    === today.toDateString();

  if (isToday) {
    return date.toLocaleTimeString(
      [],
      {
        hour: '2-digit',
        minute: '2-digit',
      },
    );
  }

  return date.toLocaleDateString(
    [],
    {
      day: 'numeric',
      month: 'short',
    },
  );
}


// =====================================================
// MESSAGE PREVIEW
// =====================================================

function messagePreview(
  body: string,
): string {
  const cleaned =
    body
      .replace(
        /\s+/g,
        ' ',
      )
      .trim();

  if (
    cleaned.length <= 110
  ) {
    return cleaned;
  }

  return `${cleaned.slice(
    0,
    110,
  )}…`;
}


// =====================================================
// MESSAGES PAGE
// =====================================================

export default function MessagesPage() {
  const [
    folder,
    setFolder,
  ] =
    useState<Folder>(
      'inbox',
    );

  const [
    messages,
    setMessages,
  ] =
    useState<MessageItem[]>(
      [],
    );

  const [
    sentMessages,
    setSentMessages,
  ] =
    useState<SentMessageItem[]>(
      [],
    );

  const [
    recipients,
    setRecipients,
  ] =
    useState<MessageRecipient[]>(
      [],
    );

  const [
    selectedMessage,
    setSelectedMessage,
  ] =
    useState<MessageItem | null>(
      null,
    );

  const [
    composeOpen,
    setComposeOpen,
  ] =
    useState(false);

  const [
    searchQuery,
    setSearchQuery,
  ] =
    useState('');

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState('');

  const [
    form,
    setForm,
  ] =
    useState({
      recipient_id: '',
      subject: '',
      body: '',
    });


  // ===================================================
  // LOAD MESSAGING DATA
  // ===================================================

  async function loadMessages() {
    setLoading(true);
    setError('');

    try {
      const [
        inboxResponse,
        sentResponse,
        recipientsResponse,
      ] =
        await Promise.all([
          api.inbox(),
          api.sentMessages(),
          api.messageRecipients(),
        ]);

      setMessages(
        inboxResponse,
      );

      setSentMessages(
        sentResponse,
      );

      setRecipients(
        recipientsResponse,
      );
    } catch (
    errorValue
    ) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to load messages.',
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(
    () => {
      void loadMessages();
    },
    [],
  );


  // ===================================================
  // COUNTS
  // ===================================================

  const unreadCount =
    messages.filter(
      (message) =>
        !message.read_at,
    ).length;


  // ===================================================
  // FILTERED INBOX
  // ===================================================

  const visibleMessages =
    useMemo(
      () => {
        let result =
          folder === 'unread'
            ? messages.filter(
              (message) =>
                !message.read_at,
            )
            : messages;

        const search =
          searchQuery
            .trim()
            .toLowerCase();

        if (!search) {
          return result;
        }

        result =
          result.filter(
            (message) =>
              [
                message.subject,
                message.body,
                message.sender_name ?? '',
              ]
                .join(' ')
                .toLowerCase()
                .includes(
                  search,
                ),
          );

        return result;
      },
      [
        folder,
        messages,
        searchQuery,
      ],
    );


  const visibleSentMessages =
    useMemo(
      () => {
        const search =
          searchQuery
            .trim()
            .toLowerCase();

        if (!search) {
          return sentMessages;
        }

        return sentMessages.filter(
          (message) =>
            [
              message.subject,
              message.body,
            ]
              .join(' ')
              .toLowerCase()
              .includes(
                search,
              ),
        );
      },
      [
        sentMessages,
        searchQuery,
      ],
    );


  // ===================================================
  // OPEN MESSAGE
  // ===================================================

  async function openMessage(
    message: MessageItem,
  ) {
    setSelectedMessage(
      message,
    );

    if (message.read_at) {
      return;
    }

    try {
      await api.markMessageRead(
        message.message_id,
      );

      const readAt =
        new Date()
          .toISOString();

      setMessages(
        (current) =>
          current.map(
            (item) =>
              item.message_id
                === message.message_id
                ? {
                  ...item,
                  read_at:
                    readAt,
                }
                : item,
          ),
      );

      setSelectedMessage(
        {
          ...message,
          read_at:
            readAt,
        },
      );
    } catch {
      // Reading the message should remain possible even
      // if the read-status update fails temporarily.
    }
  }


  // ===================================================
  // REMOVE FROM INBOX
  // ===================================================

  async function removeMessage(
    messageId: string,
  ) {
    const confirmed =
      window.confirm(
        'Remove this message from your inbox?',
      );

    if (!confirmed) {
      return;
    }

    setError('');

    try {
      await api.deleteInboxMessage(
        messageId,
      );

      setMessages(
        (current) =>
          current.filter(
            (message) =>
              message.message_id
              !== messageId,
          ),
      );

      if (
        selectedMessage
          ?.message_id
        === messageId
      ) {
        setSelectedMessage(
          null,
        );
      }
    } catch (
    errorValue
    ) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to remove message.',
      );
    }
  }


  // ===================================================
  // SEND MESSAGE
  // ===================================================

  async function sendMessage(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError('');

    if (
      !form.recipient_id
    ) {
      setError(
        'Please select a recipient.',
      );

      return;
    }

    try {
      await api.sendMessage({
        recipient_ids: [
          form.recipient_id,
        ],

        subject:
          form.subject
            .trim(),

        body:
          form.body
            .trim(),
      });

      setForm({
        recipient_id: '',
        subject: '',
        body: '',
      });

      setComposeOpen(
        false,
      );

      await loadMessages();

      setFolder(
        'sent',
      );

      setSelectedMessage(
        null,
      );
    } catch (
    errorValue
    ) {
      setError(
        errorValue instanceof Error
          ? errorValue.message
          : 'Unable to send message.',
      );
    }
  }


  // ===================================================
  // SWITCH FOLDER
  // ===================================================

  function changeFolder(
    nextFolder: Folder,
  ) {
    setFolder(
      nextFolder,
    );

    setSelectedMessage(
      null,
    );

    setSearchQuery(
      '',
    );
  }


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <>
      <PageHeader
        eyebrow="Secure communication"
        title="Messages"
        description="Private communication with your permitted MEDISCOPE contacts."
      />


      {/* =================================================
          TOP TOOLBAR
          ================================================= */}

      <section className="messages-toolbar">
        <div className="messages-search">
          <Search
            size={18}
            aria-hidden="true"
          />

          <input
            type="search"
            placeholder="Search messages"
            value={
              searchQuery
            }
            onChange={
              (event) =>
                setSearchQuery(
                  event.target.value,
                )
            }
          />
        </div>

        <button
          type="button"
          className="button primary messages-compose-button"
          onClick={
            () =>
              setComposeOpen(
                true,
              )
          }
        >
          <PenLine size={17} />
          New message
        </button>
      </section>


      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="form-error messages-page-error">
          {error}
        </div>
      )}


      {/* =================================================
          MESSAGING WORKSPACE
          ================================================= */}

      <div className="messages-layout">

        {/* ===============================================
            FOLDER RAIL
            =============================================== */}

        <aside className="messages-navigation">
          <div className="messages-navigation-label">
            Mailbox
          </div>

          <button
            type="button"
            className={
              folder === 'inbox'
                ? 'message-folder active'
                : 'message-folder'
            }
            onClick={
              () =>
                changeFolder(
                  'inbox',
                )
            }
          >
            <Inbox size={18} />

            <span>
              Inbox
            </span>

            <b>
              {messages.length}
            </b>
          </button>

          <button
            type="button"
            className={
              folder === 'unread'
                ? 'message-folder active'
                : 'message-folder'
            }
            onClick={
              () =>
                changeFolder(
                  'unread',
                )
            }
          >
            <Mail size={18} />

            <span>
              Unread
            </span>

            {
              unreadCount > 0 && (
                <b className="unread-count">
                  {unreadCount}
                </b>
              )
            }
          </button>

          <button
            type="button"
            className={
              folder === 'sent'
                ? 'message-folder active'
                : 'message-folder'
            }
            onClick={
              () =>
                changeFolder(
                  'sent',
                )
            }
          >
            <Send size={18} />

            <span>
              Sent
            </span>

            <b>
              {
                sentMessages.length
              }
            </b>
          </button>

          <div className="messages-security-note">
            <MessageSquareText
              size={18}
            />

            <div>
              <strong>
                Private workspace
              </strong>

              <span>
                Only permitted MEDISCOPE contacts can appear here.
              </span>
            </div>
          </div>
        </aside>


        {/* ===============================================
            MESSAGE CONTENT
            =============================================== */}

        <section className="messages-content">

          {/* ---------------------------------------------
              HEADER
              --------------------------------------------- */}

          <header className="messages-content-header">
            <div>
              <span className="eyebrow">
                {
                  folder === 'inbox'
                    ? 'Inbox'
                    : folder === 'unread'
                      ? 'Unread'
                      : 'Sent'
                }
              </span>

              <h2>
                {
                  folder === 'sent'
                    ? `${visibleSentMessages.length} sent message${visibleSentMessages.length === 1
                      ? ''
                      : 's'
                    }`
                    : `${visibleMessages.length} message${visibleMessages.length === 1
                      ? ''
                      : 's'
                    }`
                }
              </h2>
            </div>
          </header>


          {/* ---------------------------------------------
              LOADING
              --------------------------------------------- */}

          {loading && (
            <div className="messages-empty-state">
              <div className="messages-empty-icon">
                <MailOpen size={24} />
              </div>

              <h3>
                Loading messages
              </h3>

              <p>
                Retrieving your secure mailbox.
              </p>
            </div>
          )}


          {/* ---------------------------------------------
              SENT MESSAGES
              --------------------------------------------- */}

          {!loading &&
            folder === 'sent' && (
              <div className="messages-list">
                {
                  visibleSentMessages.length
                    === 0
                    ? (
                      <div className="messages-empty-state">
                        <div className="messages-empty-icon">
                          <Send size={24} />
                        </div>

                        <h3>
                          No sent messages
                        </h3>

                        <p>
                          Messages you send will appear here.
                        </p>
                      </div>
                    )
                    : visibleSentMessages.map(
                      (
                        message,
                      ) => (
                        <article
                          key={
                            message.id
                          }
                          className="message-card sent"
                        >
                          <div className="message-card-icon sent">
                            <Send size={16} />
                          </div>

                          <div className="message-card-main">
                            <div className="message-card-heading">
                              <strong>
                                {
                                  message.subject
                                }
                              </strong>

                              <time>
                                {
                                  formatMessageDate(
                                    message.created_at,
                                  )
                                }
                              </time>
                            </div>

                            <p>
                              {
                                messagePreview(
                                  message.body,
                                )
                              }
                            </p>
                          </div>
                        </article>
                      ),
                    )
                }
              </div>
            )}


          {/* ---------------------------------------------
              SELECTED MESSAGE
              --------------------------------------------- */}

          {!loading &&
            folder !== 'sent' &&
            selectedMessage && (
              <article className="message-reader">

                <div className="message-reader-toolbar">
                  <button
                    type="button"
                    className="message-reader-back"
                    onClick={
                      () =>
                        setSelectedMessage(
                          null,
                        )
                    }
                  >
                    <ArrowLeft size={17} />
                    Back
                  </button>

                  <button
                    type="button"
                    className="icon-button danger"
                    title="Remove from inbox"
                    aria-label="Remove from inbox"
                    onClick={
                      () =>
                        removeMessage(
                          selectedMessage.message_id,
                        )
                    }
                  >
                    <Trash2 size={17} />
                  </button>
                </div>


                <header className="message-reader-header">
                  <div className="message-reader-avatar">
                    {
                      (
                        selectedMessage.sender_name
                        ??
                        'M'
                      )
                        .charAt(0)
                        .toUpperCase()
                    }
                  </div>

                  <div>
                    <span>
                      From
                    </span>

                    <strong>
                      {
                        selectedMessage.sender_name
                        ??
                        'MEDISCOPE'
                      }
                    </strong>

                    <time>
                      {
                        new Date(
                          selectedMessage.created_at,
                        ).toLocaleString()
                      }
                    </time>
                  </div>
                </header>


                <div className="message-reader-title">
                  <h1>
                    {
                      selectedMessage.subject
                    }
                  </h1>
                </div>


                <div className="message-reader-body">
                  {
                    selectedMessage.body
                  }
                </div>
              </article>
            )}


          {/* ---------------------------------------------
              INBOX / UNREAD LIST
              --------------------------------------------- */}

          {!loading &&
            folder !== 'sent' &&
            !selectedMessage && (
              <div className="messages-list">
                {
                  visibleMessages.length
                    === 0
                    ? (
                      <div className="messages-empty-state">
                        <div className="messages-empty-icon">
                          {
                            folder === 'unread'
                              ? (
                                <MailOpen size={24} />
                              )
                              : (
                                <Inbox size={24} />
                              )
                          }
                        </div>

                        <h3>
                          {
                            folder === 'unread'
                              ? 'You’re all caught up'
                              : 'Your inbox is clear'
                          }
                        </h3>

                        <p>
                          {
                            folder === 'unread'
                              ? 'There are no unread messages at the moment.'
                              : 'New messages will appear here.'
                          }
                        </p>
                      </div>
                    )
                    : visibleMessages.map(
                      (
                        message,
                      ) => {
                        const unread =
                          !message.read_at;

                        return (
                          <article
                            key={
                              message.message_id
                            }
                            className={
                              unread
                                ? 'message-card unread'
                                : 'message-card'
                            }
                          >
                            <button
                              type="button"
                              className="message-card-open"
                              onClick={
                                () =>
                                  openMessage(
                                    message,
                                  )
                              }
                            >
                              <div className="message-card-avatar">
                                {
                                  (
                                    message.sender_name
                                    ??
                                    'M'
                                  )
                                    .charAt(0)
                                    .toUpperCase()
                                }
                              </div>

                              <div className="message-card-main">
                                <div className="message-card-heading">
                                  <strong>
                                    {
                                      message.sender_name
                                      ??
                                      'MEDISCOPE'
                                    }
                                  </strong>

                                  <time>
                                    {
                                      formatMessageDate(
                                        message.created_at,
                                      )
                                    }
                                  </time>
                                </div>

                                <div className="message-card-subject">
                                  <h3>
                                    {
                                      message.subject
                                    }
                                  </h3>

                                  {
                                    unread && (
                                      <span className="unread-indicator">
                                        New
                                      </span>
                                    )
                                  }
                                </div>

                                <p>
                                  {
                                    messagePreview(
                                      message.body,
                                    )
                                  }
                                </p>
                              </div>
                            </button>

                            <button
                              type="button"
                              className="message-card-action"
                              title="Remove from inbox"
                              aria-label="Remove from inbox"
                              onClick={
                                () =>
                                  removeMessage(
                                    message.message_id,
                                  )
                              }
                            >
                              <MoreHorizontal size={18} />
                            </button>
                          </article>
                        );
                      },
                    )
                }
              </div>
            )}
        </section>
      </div>


      {/* =================================================
          COMPOSE MODAL
          ================================================= */}

      {composeOpen && (
        <div
          className="compose-backdrop"
          role="presentation"
          onMouseDown={
            (event) => {
              if (
                event.target
                === event.currentTarget
              ) {
                setComposeOpen(
                  false,
                );
              }
            }
          }
        >
          <form
            className="compose-sheet"
            onSubmit={
              sendMessage
            }
          >
            <header className="compose-sheet-header">
              <div>
                <span className="eyebrow">
                  Secure message
                </span>

                <h2>
                  New message
                </h2>

                <p>
                  Send a private message to an approved MEDISCOPE contact.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                title="Close"
                aria-label="Close compose window"
                onClick={
                  () =>
                    setComposeOpen(
                      false,
                    )
                }
              >
                <X size={18} />
              </button>
            </header>


            <div className="compose-sheet-body">
              <label>
                <span>
                  To
                </span>

                <select
                  required
                  value={
                    form.recipient_id
                  }
                  onChange={
                    (event) =>
                      setForm({
                        ...form,

                        recipient_id:
                          event.target.value,
                      })
                  }
                >
                  <option value="">
                    Choose a recipient
                  </option>

                  {
                    recipients.map(
                      (
                        recipient,
                      ) => (
                        <option
                          key={
                            recipient.id
                          }
                          value={
                            recipient.id
                          }
                        >
                          {
                            recipient.first_name
                          }{' '}
                          {
                            recipient.last_name
                          }
                          {' · '}
                          {
                            recipient.role
                          }
                        </option>
                      ),
                    )
                  }
                </select>
              </label>


              <label>
                <span>
                  Subject
                </span>

                <input
                  required
                  minLength={1}
                  maxLength={255}
                  placeholder="What is this message about?"
                  value={
                    form.subject
                  }
                  onChange={
                    (event) =>
                      setForm({
                        ...form,

                        subject:
                          event.target.value,
                      })
                  }
                />
              </label>


              <label>
                <span>
                  Message
                </span>

                <textarea
                  required
                  rows={9}
                  maxLength={10000}
                  placeholder="Write your message…"
                  value={
                    form.body
                  }
                  onChange={
                    (event) =>
                      setForm({
                        ...form,

                        body:
                          event.target.value,
                      })
                  }
                />

                <small>
                  {
                    form.body.length
                  } / 10,000
                </small>
              </label>
            </div>


            <footer className="compose-sheet-footer">
              <button
                type="button"
                className="button secondary"
                onClick={
                  () =>
                    setComposeOpen(
                      false,
                    )
                }
              >
                Cancel
              </button>

              <button
                type="submit"
                className="button primary"
              >
                <Send size={17} />
                Send message
              </button>
            </footer>
          </form>
        </div>
      )}
    </>
  );
}
