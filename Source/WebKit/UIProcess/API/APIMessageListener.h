/*
 * Copyright (C) 2019 Apple Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. AND ITS CONTRIBUTORS ``AS IS''
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL APPLE INC. OR ITS CONTRIBUTORS
 * BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGE.
 */

#pragma once

#include "APIObject.h"
#include <wtf/CompletionHandler.h>

namespace API {

class MessageListener : public ObjectImpl<Object::Type::MessageListener> {
    WTF_MAKE_NONCOPYABLE(MessageListener);
public:
    static Ref<MessageListener> create(CompletionHandler<void(RefPtr<API::Object>)>&& reply)
    {
        return adoptRef(*new MessageListener(WTFMove(reply)));
    }

    void sendReply(RefPtr<API::Object>&& reply)
    {
        m_reply(WTFMove(reply));
    }

private:
    MessageListener(CompletionHandler<void(RefPtr<API::Object>)>&& reply)
        : m_reply(WTFMove(reply)) { }

    CompletionHandler<void(RefPtr<API::Object>)> m_reply;
};

} // namespace API

SPECIALIZE_TYPE_TRAITS_API_OBJECT(MessageListener);
