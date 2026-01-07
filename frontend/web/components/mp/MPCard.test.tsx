import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MPCard, { MP } from '../../../frontend/web/components/mp/MPCard';

describe('MPCard Component', () => {
    const mockMP: MP = {
        id: 'mp001',
        name: 'Hon. John Mbadi',
        constituency: 'Suba South',
        party: 'ODM',
        performanceScore: 85
    };

    test('renders MP information correctly', () => {
        render(<MPCard mp={mockMP} />);

        expect(screen.getByTestId('mp-name')).toHaveTextContent('Hon. John Mbadi');
        expect(screen.getByTestId('constituency-party')).toHaveTextContent('Suba South • ODM');
        expect(screen.getByTestId('performance-score')).toHaveTextContent('85/100');
    });

    test('calls onSelect when clicked', () => {
        const mockOnSelect = jest.fn();
        render(<MPCard mp={mockMP} onSelect={mockOnSelect} />);

        fireEvent.click(screen.getByTestId(`mp-card-${mockMP.id}`));
        expect(mockOnSelect).toHaveBeenCalledWith(mockMP);
    });

    test('hides performance score when showPerformanceScore is false', () => {
        render(<MPCard mp={mockMP} showPerformanceScore={false} />);

        expect(screen.queryByTestId('performance-score')).not.toBeInTheDocument();
    });

    test('shows party indicator with correct color', () => {
        render(<MPCard mp={mockMP} />);

        const partyIndicator = screen.getByTestId('party-indicator');
        expect(partyIndicator).toBeInTheDocument();
        expect(partyIndicator).toHaveStyle('background-color: #4A90E2'); // ODM blue
    });

    test('handles MP without performance score', () => {
        const mpWithoutScore: MP = {
            id: 'mp002',
            name: 'Hon. Test MP',
            constituency: 'Test Constituency',
            party: 'UDA'
        };

        render(<MPCard mp={mpWithoutScore} />);

        expect(screen.getByTestId('mp-name')).toHaveTextContent('Hon. Test MP');
        expect(screen.queryByTestId('performance-score')).not.toBeInTheDocument();
    });

    test('applies correct performance score color classes', () => {
        const highScoreMP: MP = { ...mockMP, performanceScore: 92 };
        const { rerender } = render(<MPCard mp={highScoreMP} />);

        expect(screen.getByTestId('performance-score')).toHaveClass('text-green-600');

        const mediumScoreMP: MP = { ...mockMP, performanceScore: 65 };
        rerender(<MPCard mp={mediumScoreMP} />);
        expect(screen.getByTestId('performance-score')).toHaveClass('text-yellow-600');

        const lowScoreMP: MP = { ...mockMP, performanceScore: 45 };
        rerender(<MPCard mp={lowScoreMP} />);
        expect(screen.getByTestId('performance-score')).toHaveClass('text-red-600');
    });

    test('uses default party color for unknown party', () => {
        const unknownPartyMP: MP = {
            ...mockMP,
            party: 'UNKNOWN_PARTY'
        };

        render(<MPCard mp={unknownPartyMP} />);

        const partyIndicator = screen.getByTestId('party-indicator');
        expect(partyIndicator).toHaveStyle('background-color: #6B7280'); // Default gray
    });

    test('accessibility: has proper click handling', () => {
        const mockOnSelect = jest.fn();
        render(<MPCard mp={mockMP} onSelect={mockOnSelect} />);

        const card = screen.getByTestId(`mp-card-${mockMP.id}`);
        expect(card).toHaveClass('cursor-pointer');

        // Test keyboard interaction would go here in a real implementation
        fireEvent.click(card);
        expect(mockOnSelect).toHaveBeenCalled();
    });
});
