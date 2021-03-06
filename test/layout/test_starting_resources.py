import pytest

from randovania.bitpacking import bitpacking
from randovania.game_description import default_database
from randovania.layout.starting_resources import StartingResources, StartingResourcesConfiguration


@pytest.fixture(params=[config for config in StartingResourcesConfiguration
                        if config != StartingResourcesConfiguration.CUSTOM],
                name="simple_starting_resources")
def _simple_starting_resources(request):
    yield StartingResources.from_non_custom_configuration(request.param)


@pytest.fixture(name="all_zero_starting_resources")
def _all_zero_starting_resources():
    database = default_database.default_prime2_resource_database()
    return StartingResources(StartingResourcesConfiguration.CUSTOM,
                             {item: 0 for item in database.item})


def test_default():
    value = StartingResources.default()

    # Assert
    assert value.configuration == StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED


def test_round_trip_json_simple(simple_starting_resources):
    # Run
    round_trip = StartingResources.from_json(simple_starting_resources.as_json)

    # Assert
    assert simple_starting_resources == round_trip


def test_round_trip_json_all_zero_items(all_zero_starting_resources):
    # Run
    round_trip = StartingResources.from_json(all_zero_starting_resources.as_json)

    # Assert
    assert all_zero_starting_resources == round_trip


def test_round_trip_bitpack_simple(simple_starting_resources):
    # Run
    round_trip = bitpacking.round_trip(simple_starting_resources)

    # Assert
    assert simple_starting_resources == round_trip


def test_round_trip_bitpack_all_zero_items(all_zero_starting_resources):
    # Run
    round_trip = bitpacking.round_trip(all_zero_starting_resources)

    # Assert
    assert all_zero_starting_resources == round_trip


def test_non_custom_with_custom_should_raise():
    with pytest.raises(ValueError) as err:
        StartingResources.from_non_custom_configuration(StartingResourcesConfiguration.CUSTOM)

    assert str(err.value) == "from_non_custom_configuration shouldn't receive CUSTOM configuration"


def test_missing_item_for_constructor_should_raise():
    with pytest.raises(ValueError) as err:
        StartingResources(StartingResourcesConfiguration.CUSTOM, {})

    assert str(err.value).startswith("resources {} has missing items: ")


def test_raise_for_pickup_above_maximum():
    database = default_database.default_prime2_resource_database()

    with pytest.raises(ValueError) as err:
        StartingResources(StartingResourcesConfiguration.CUSTOM,
                          {item: 10 for item in database.item})

    assert str(err.value) == "Item I: Power Beam has a maximum of 1, got 10"
