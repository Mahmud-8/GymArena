package com.gymarena.membership;

/** Renewal outbox published through IMembership and consumed by Notifications (FR-04.3). */
public interface IRenewalFeed {
    void publish(RenewalChanged change);
}
