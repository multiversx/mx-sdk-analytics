from enum import Enum

from multiversx_usage_analytics_tool.ecosystem import Organization
from multiversx_usage_analytics_tool.utils import PackagesRegistry


class EcosystemConfiguration(Enum):
    MULTIVERSX = Organization(
        name='Multiversx',
        search_includes={
            PackagesRegistry.NPM: '@multiversx/sdk',
            PackagesRegistry.CARGO: 'multiversx',
            PackagesRegistry.PYPI: 'multiversx-sdk',
            PackagesRegistry.GITHUB: 'sdk',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='multiversx',
        gather_data=True,
    )
    SOLANA = Organization(
        name='Solana',
        search_includes={
            PackagesRegistry.NPM: '@solana',
            PackagesRegistry.CARGO: 'solana',
            PackagesRegistry.PYPI: 'solana',
            PackagesRegistry.GITHUB: '',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='solana-labs',
        affiliated_orgs=['anza-xyz', 'michaelhly'],
        gather_data=False,
    )
    NEAR = Organization(
        name='Near',
        search_includes={
            PackagesRegistry.NPM: 'near-',
            PackagesRegistry.CARGO: 'near-',
            PackagesRegistry.PYPI: 'near',
            PackagesRegistry.GITHUB: 'near',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='near',
        gather_data=False,
    )
    AVALANCHE = Organization(
        name='Avalanche',
        search_includes={
            PackagesRegistry.NPM: '@avalabs/',
            PackagesRegistry.CARGO: 'avalanche',
            PackagesRegistry.PYPI: 'avalanche',
            PackagesRegistry.GITHUB: '',
        },
        search_excludes={
            PackagesRegistry.GITHUB: 'deprecated'
        },
        github_organization='ava-labs',
        gather_data=True
    )
