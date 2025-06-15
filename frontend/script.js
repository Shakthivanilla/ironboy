const API_BASE_URL = 'http://127.0.0.1:5000';

// DOM Element Selectors
const transactionForm = document.getElementById('transaction-form');
const dateInput = document.getElementById('date');
const descriptionInput = document.getElementById('description');
const amountInput = document.getElementById('amount');
const typeInput = document.getElementById('type');
const categorySelect = document.getElementById('category');
const transactionsTbody = document.getElementById('transactions-tbody');
const totalIncomeSpan = document.getElementById('total-income');
const totalExpensesSpan = document.getElementById('total-expenses');
const netBalanceSpan = document.getElementById('net-balance');
const submitButton = document.querySelector('#transaction-form button[type="submit"]');


let currentEditingId = null; // Used to track if we are editing an existing transaction

// Helper for formatting currency
function formatCurrency(amount) {
    return parseFloat(amount).toFixed(2);
}

// 1. Fetch and Populate Categories
async function fetchCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const categories = await response.json();
        populateCategoryDropdown(categories);
    } catch (error) {
        console.error('Error fetching categories:', error);
        categorySelect.innerHTML = '<option value="">Error loading categories</option>';
    }
}

function populateCategoryDropdown(categories) {
    categorySelect.innerHTML = '<option value="">Select a category</option>'; // Clear existing and add placeholder
    if (categories && categories.length > 0) {
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });
    } else {
        categorySelect.innerHTML = '<option value="">No categories available</option>';
    }
}

// 2. Fetch and Display Balance
async function fetchBalance() {
    try {
        const response = await fetch(`${API_BASE_URL}/balance`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const balance = await response.json();
        totalIncomeSpan.textContent = formatCurrency(balance.total_income);
        totalExpensesSpan.textContent = formatCurrency(balance.total_expense);
        netBalanceSpan.textContent = formatCurrency(balance.net_balance);
    } catch (error) {
        console.error('Error fetching balance:', error);
        totalIncomeSpan.textContent = 'Error';
        totalExpensesSpan.textContent = 'Error';
        netBalanceSpan.textContent = 'Error';
    }
}

// 3. Fetch and Display Transactions
async function fetchTransactions() {
    try {
        const response = await fetch(`${API_BASE_URL}/transactions`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const transactions = await response.json();
        renderTransactions(transactions);
    } catch (error) {
        console.error('Error fetching transactions:', error);
        transactionsTbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Error loading transactions.</td></tr>';
    }
}

function renderTransactions(transactions) {
    transactionsTbody.innerHTML = ''; // Clear existing rows

    if (transactions && transactions.length > 0) {
        transactions.forEach(transaction => {
            const row = transactionsTbody.insertRow();
            row.insertCell().textContent = transaction.date;
            row.insertCell().textContent = transaction.description;
            row.insertCell().textContent = transaction.category_name; // From backend JOIN
            row.insertCell().textContent = transaction.type.charAt(0).toUpperCase() + transaction.type.slice(1); // Capitalize
            const amountCell = row.insertCell();
            amountCell.textContent = formatCurrency(transaction.amount);
            amountCell.style.textAlign = 'right'; // Align amount to right

            // Actions cell
            const actionsCell = row.insertCell();
            actionsCell.style.textAlign = 'center';

            const editButton = document.createElement('button');
            editButton.classList.add('edit-btn');
            editButton.textContent = 'Edit';
            // Store entire transaction data for easier form population
            editButton.dataset.transaction = JSON.stringify(transaction);
            editButton.addEventListener('click', () => populateFormForEdit(transaction));
            actionsCell.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.classList.add('delete-btn');
            deleteButton.textContent = 'Delete';
            deleteButton.dataset.transactionId = transaction.id;
            deleteButton.addEventListener('click', () => handleDeleteTransaction(transaction.id));
            actionsCell.appendChild(deleteButton);
        });
    } else {
        // Updated colspan to 6 due to new "Actions" column
        transactionsTbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No transactions yet.</td></tr>';
    }
}

// 4. Combined Initial Load Function
async function initialLoad() {
    await fetchCategories(); // Wait for categories to load for the form
    await fetchTransactions();
    await fetchBalance();
}

// 5. Handle Add Transaction Form Submission
async function handleAddTransaction(event) {
    event.preventDefault();

    const date = dateInput.value;
    const description = descriptionInput.value.trim();
    const amount = parseFloat(amountInput.value);
    const type = typeInput.value;
    const categoryId = categorySelect.value;

    // Basic validation
    if (!date || !description || isNaN(amount) || amount <= 0 || !type || !categoryId) {
        alert('Please fill in all fields correctly. Amount must be positive.');
        return;
    }

    const transactionData = {
        date: date,
        description: description,
        type: type,
        amount: amount,
        category_id: parseInt(categoryId)
    };

    let method = 'POST';
    let url = `${API_BASE_URL}/transactions`;

    if (currentEditingId) {
        method = 'PUT';
        url = `${API_BASE_URL}/transactions/${currentEditingId}`;
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(transactionData),
        });

        if (response.ok) {
            // const result = await response.json();
            // console.log(`Transaction ${currentEditingId ? 'updated' : 'added'}:`, result);

            currentEditingId = null; // Reset editing state
            if(submitButton) submitButton.textContent = 'Add Transaction';
            transactionForm.reset();

            // Instead of full initialLoad, just refresh transactions and balance
            await fetchTransactions();
            await fetchBalance();
        } else {
            const errorData = await response.json();
            console.error(`Error ${currentEditingId ? 'updating' : 'adding'} transaction:`, errorData);
            alert(`Error ${currentEditingId ? 'updating' : 'adding'} transaction: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error(`Network or other error ${currentEditingId ? 'updating' : 'adding'} transaction:`, error);
        alert(`An error occurred. Check console for details.`);
    }
}

// 3. Implement handleDeleteTransaction(transactionId)
async function handleDeleteTransaction(transactionId) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            // console.log('Transaction deleted successfully');
            // Refresh data after deletion
            await fetchTransactions();
            await fetchBalance();
            // If the deleted transaction was being edited, reset the form
            if (currentEditingId === transactionId) {
                currentEditingId = null;
                if(submitButton) submitButton.textContent = 'Add Transaction';
                transactionForm.reset();
            }
        } else {
            const errorData = await response.json();
            console.error('Error deleting transaction:', errorData);
            alert(`Error deleting transaction: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Network or other error deleting transaction:', error);
        alert('An error occurred while deleting the transaction. Check console for details.');
    }
}

// 4. Implement populateFormForEdit(transaction)
function populateFormForEdit(transaction) {
    currentEditingId = transaction.id;
    dateInput.value = transaction.date;
    descriptionInput.value = transaction.description;
    amountInput.value = transaction.amount;
    typeInput.value = transaction.type;

    // Ensure category ID is correctly matched, as category_name is what's directly in transaction object from GET /transactions
    // We need to find the category ID from the full category list if category_id is not directly available
    // However, our GET /transactions joins category_id, so it should be there.
    // If not, an alternative is to use find by name on the categories loaded in dropdown
    if (transaction.category_id) {
        categorySelect.value = transaction.category_id;
    } else { // Fallback if category_id wasn't in the transaction object (should not happen with current backend)
        const categoryOption = Array.from(categorySelect.options).find(opt => opt.text === transaction.category_name);
        if (categoryOption) categorySelect.value = categoryOption.value;
    }

    if(submitButton) submitButton.textContent = 'Update Transaction';
    transactionForm.scrollIntoView({ behavior: 'smooth' });
}


// Event Listeners
document.addEventListener('DOMContentLoaded', initialLoad);
if (transactionForm) {
    transactionForm.addEventListener('submit', handleAddTransaction);
} else {
    console.error("Transaction form not found on page load.");
}
