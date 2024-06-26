import { registry } from "@web/core/registry";

/**
 * Verify that a user can modify their own profile information.
 */
registry.category("web_tour.tours").add("mail/static/tests/tours/user_modify_own_profile_tour.js", {
    test: true,
    steps: () => [
        {
            content: "Open user account menu",
            trigger: ".o_user_menu button",
            run: "click",
        },
        {
            content: "Open preferences / profile screen",
            trigger: "[data-menu=settings]",
            run: "click",
        },
        {
            content: "Update the email address",
            trigger: 'div[name="email"] input',
            run: "edit updatedemail@example.com",
        },
        {
            trigger: "body.modal-open",
        },
        {
            content: "Save the form",
            trigger: 'button[name="preference_save"]',
        },
        {
            content: "Wait until the modal is closed",
            trigger: "body:not(.modal-open)",
        },
    ],
});
