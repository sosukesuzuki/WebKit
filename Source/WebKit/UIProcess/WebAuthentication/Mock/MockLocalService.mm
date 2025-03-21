/*
 * Copyright (C) 2018 Apple Inc. All rights reserved.
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

#import "config.h"
#import "MockLocalService.h"

#if ENABLE(WEB_AUTHN)

#import "LocalAuthenticator.h"
#import "MockLocalConnection.h"
#import <wtf/RunLoop.h>

#if USE(APPLE_INTERNAL_SDK)
#import <WebKitAdditions/MockLocalServiceAdditions.h>
#else
#define MOCK_LOCAL_SERVICE_ADDITIONS
#endif

namespace WebKit {

Ref<MockLocalService> MockLocalService::create(AuthenticatorTransportServiceObserver& observer, const WebCore::MockWebAuthenticationConfiguration& configuration)
{
    return adoptRef(*new MockLocalService(observer, configuration));
}

MockLocalService::MockLocalService(AuthenticatorTransportServiceObserver& observer, const WebCore::MockWebAuthenticationConfiguration& configuration)
    : LocalService(observer)
    , m_configuration(configuration)
{
MOCK_LOCAL_SERVICE_ADDITIONS
}

bool MockLocalService::platformStartDiscovery() const
{
    return !!m_configuration.local;
}

Ref<LocalConnection> MockLocalService::createLocalConnection() const
{
    return MockLocalConnection::create(m_configuration);
}

} // namespace WebKit

#endif // ENABLE(WEB_AUTHN)
