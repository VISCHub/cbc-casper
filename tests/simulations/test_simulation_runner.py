import sys
import pytest

from casper.protocols.blockchain.blockchain_protocol import BlockchainProtocol
from casper.protocols.binary.binary_protocol import BinaryProtocol

from casper.network import Network
from casper.networks import StepNetwork
from simulations.simulation_runner import SimulationRunner
import simulations.utils as utils


@pytest.mark.parametrize(
    'protocol, mode, rounds, report_interval',
    [
        (BinaryProtocol, 'rand', 10, 2),
        (BlockchainProtocol, 'rand', 10, 1),
        (BlockchainProtocol, 'rrob', None, None),
        (BinaryProtocol, 'rrob', None, None),
    ]
)
def test_new_simulation_runner(generate_validator_set, protocol, mode, rounds, report_interval):
    msg_gen = utils.message_maker(mode)
    validator_set = generate_validator_set(protocol)
    network = StepNetwork(validator_set, protocol)

    simulation_runner = SimulationRunner(
        validator_set,
        msg_gen,
        protocol,
        network,
        rounds,
        report_interval,
        False,
        False
    )

    assert simulation_runner.validator_set == validator_set
    assert simulation_runner.msg_gen == msg_gen
    assert simulation_runner.round == 0
    assert isinstance(simulation_runner.network, Network)

    if rounds:
        assert simulation_runner.total_rounds == rounds
    else:
        assert simulation_runner.total_rounds == sys.maxsize

    if report_interval:
        assert simulation_runner.report_interval == report_interval
    else:
        assert simulation_runner.report_interval == 1


@pytest.mark.parametrize(
    'rounds',
    [
        (3),
        (10),
    ]
)
def test_simulation_runner_run(simulation_runner, rounds):
    simulation_runner.total_rounds = rounds
    assert simulation_runner.round == 0

    simulation_runner.run()

    assert simulation_runner.round == rounds


def test_simulation_runner_step(simulation_runner):
    assert simulation_runner.round == 0
    simulation_runner.step()
    assert simulation_runner.round == 1

    for i in range(5):
        simulation_runner.step()

    assert simulation_runner.round == 6


@pytest.mark.parametrize(
    'protocol, mode, messages_generated_per_round, potential_extra_messages',
    [
        (BlockchainProtocol, 'rand', 1, 4),
        (BlockchainProtocol, 'rrob', 1, 4),
        (BlockchainProtocol, 'full', 5, 4),
        (BlockchainProtocol, 'nofinal', 2, 2),
        (BinaryProtocol, 'rand', 1, 0),
        (BinaryProtocol, 'rrob', 1, 0),
        (BinaryProtocol, 'full', 5, 0),
        (BinaryProtocol, 'nofinal', 2, 0),
    ]
)
def test_simulation_runner_send_messages(
        generate_validator_set,
        protocol,
        mode,
        messages_generated_per_round,
        potential_extra_messages
        ):
    msg_gen = utils.message_maker(mode)
    validator_set = generate_validator_set(protocol)
    network = StepNetwork(validator_set, protocol)

    simulation_runner = SimulationRunner(
        validator_set,
        msg_gen,
        protocol,
        network,
        100,
        20,
        False,
        False
    )

    if protocol == BlockchainProtocol:
        assert len(simulation_runner.network.global_view.justified_messages) == 1
    if protocol == BinaryProtocol:
        assert len(simulation_runner.network.global_view.justified_messages) == len(validator_set)

    initial_message_length = len(simulation_runner.network.global_view.justified_messages)
    for i in range(10):
        simulation_runner.step()
        assert len(simulation_runner.network.global_view.justified_messages) <= \
            initial_message_length + potential_extra_messages + (i+1)*messages_generated_per_round
