from builder import actions
from opencodelists.tests.factories import UserFactory


def test_create_draft():
    # Arrange: create a user
    owner = UserFactory()

    # Act: create a draft
    draft = actions.create_draft(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Assert...
    # that a draft's attributes have been set
    assert draft.owner == owner
    assert draft.name == "Test Codelist"
    assert draft.slug == "test-codelist"
    assert draft.coding_system_id == "snomedct"


def test_create_draft_with_codes():
    # Arrange: create a user
    owner = UserFactory()

    # Act: create a draft with codes
    draft = actions.create_draft_with_codes(
        owner=owner,
        name="Test Codelist",
        coding_system_id="snomedct",
        codes=["1067731000000107", "1068181000000106"],
    )

    # Assert...
    # that a draft's attributes have been set
    assert draft.owner == owner
    assert draft.name == "Test Codelist"
    assert draft.slug == "test-codelist"
    assert draft.coding_system_id == "snomedct"
    assert draft.code_objs.count() == 2


def test_create_search():
    # Arrange: create a draft
    owner = UserFactory()
    draft = actions.create_draft(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Act: create a first search
    s = actions.create_search(
        draft=draft, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Assert...
    # that the search's attributes have been set
    assert s.draft == draft
    assert s.term == "swimming"
    assert s.slug == "swimming"

    # that the newly created search has 2 results
    assert s.results.count() == 2
    # that the draft has 1 search
    assert draft.searches.count() == 1
    # that the draft has 2 codes
    assert draft.code_objs.count() == 2

    # Act: create another search
    s = actions.create_search(
        draft=draft, term="synchronised", codes=["1068181000000106"]
    )

    # Assert...
    # that the newly created search has 1 result
    assert s.results.count() == 1
    # that the draft has 2 searches
    assert draft.searches.count() == 2
    # that the draft still has 2 codes
    assert draft.code_objs.count() == 2


def test_delete_search():
    # Arrange: create a draft with codes and a search
    owner = UserFactory()
    draft = actions.create_draft_with_codes(
        owner=owner,
        name="Test Codelist",
        coding_system_id="snomedct",
        codes=["1067731000000107", "1068181000000106"],
    )
    s = actions.create_search(
        draft=draft, term="synchronised", codes=["1068181000000106"]
    )

    # Act: delete the search
    actions.delete_search(search=s)

    # Assert...
    # that the draft has 0 searches
    assert draft.searches.count() == 0
    # that the still draft has 1 code which doesn't belong to a search
    assert draft.code_objs.count() == 1

    # Arrange: create new searches
    s1 = actions.create_search(
        draft=draft, term="synchronised", codes=["1068181000000106"]
    )
    s2 = actions.create_search(
        draft=draft, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Act: delete the search for "swimming"
    actions.delete_search(search=s2)

    # Assert...
    # that the draft has only 1 search
    assert draft.searches.count() == 1
    # that the draft has only 1 code
    assert draft.code_objs.count() == 1

    # Arrange: recreate the search for "swimming"
    actions.create_search(
        draft=draft, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Act: delete the search for "synchronised"
    actions.delete_search(search=s1)

    # Assert...
    # that the draft has only 1 search
    assert draft.searches.count() == 1
    # that the draft still has both codes
    assert draft.code_objs.count() == 2


def test_update_code_statuses(tennis_elbow):
    # Arrange: load fixtures and create a draft with a search
    owner = UserFactory()
    draft = actions.create_draft(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Search results have this structure in hierarchy
    #
    # 116309007 Finding of elbow region
    #     128133004 Disorder of elbow
    #         239964003 Soft tissue lesion of elbow region
    #         35185008 Enthesopathy of elbow region
    #             73583000 Epicondylitis
    #                 202855006 Lateral epicondylitis
    #         429554009 Arthropathy of elbow
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    #     298869002 Finding of elbow joint
    #         298163003 Elbow joint inflamed
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    #         429554009 Arthropathy of elbow
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    actions.create_search(
        draft=draft,
        term="elbow",
        codes=[
            "116309007",  # Finding of elbow region
            "128133004",  # Disorder of elbow
            "239964003",  # Soft tissue lesion of elbow region
            "35185008",  # Enthesopathy of elbow region
            "73583000",  # Epicondylitis
            "202855006",  # Lateral epicondylitis
            "429554009",  # Arthropathy of elbow
            "439656005",  # Arthritis of elbow
            "298869002",  # Finding of elbow joint
            "298163003",  # Elbow joint inflamed
        ],
    )

    # Act: process single update from the client
    actions.update_code_statuses(draft=draft, updates=[("35185008", "+")])

    # Assert that results have the expected status
    assert dict(draft.code_objs.values_list("code", "status")) == {
        "116309007": "?",  # Finding of elbow region
        "128133004": "?",  # Disorder of elbow
        "239964003": "?",  # Soft tissue lesion of elbow region
        "35185008": "+",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "202855006": "(+)",  # Lateral epicondylitis
        "429554009": "?",  # Arthropathy of elbow
        "439656005": "?",  # Arthritis of elbow
        "298869002": "?",  # Finding of elbow joint
        "298163003": "?",  # Elbow joint inflamed
    }

    # Act: process multiple updates from the client
    actions.update_code_statuses(
        draft=draft, updates=[("35185008", "-"), ("116309007", "+"), ("35185008", "?")]
    )

    # Assert that results have the expected status
    assert dict(draft.code_objs.values_list("code", "status")) == {
        "116309007": "+",  # Finding of elbow region
        "128133004": "(+)",  # Disorder of elbow
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "202855006": "(+)",  # Lateral epicondylitis
        "429554009": "(+)",  # Arthropathy of elbow
        "439656005": "(+)",  # Arthritis of elbow
        "298869002": "(+)",  # Finding of elbow joint
        "298163003": "(+)",  # Elbow joint inflamed
    }
