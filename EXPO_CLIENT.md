# Finze API Client Integration

## React Native/Expo Integration Guide

Complete integration guide for connecting your React Native/Expo frontend to the Finze backend API. Includes AI expense categorization and receipt scanning with Google Gemini AI.

### Features Included
- 🤖 **AI Expense Categorization** - Automatic expense categorization with 98%+ accuracy
- 📸 **Receipt Scanning** - Extract expense data from receipt photos
- 💾 **Expense Management** - Save, update, delete, and retrieve expenses
- 📊 **Analytics** - User spending summaries and category statistics
- 🎯 **Active Learning** - Submit corrections to improve AI accuracy

### API Service Class

```javascript
// services/FinzeAPI.js
const API_BASE_URL = 'http://YOUR_SERVER_IP:8001'; // Update this!

export class FinzeAPI {
  
  // =====================
  // AI CATEGORIZATION APIs
  // =====================
  
  static async categorizeExpense(description, amount, merchant_name = '') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/categorize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description || '',
          amount: parseFloat(amount) || null,
          merchant_name: merchant_name || ''
        })
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error categorizing expense:', error);
      throw error;
    }
  }
  
  static async categorizeExpenses(expenses) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/categorize-batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: expenses })
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      const result = await response.json();
      return result.results;
    } catch (error) {
      console.error('Error batch categorizing:', error);
      throw error;
    }
  }
  
  static async submitCorrection(description, correct_category, amount = null, merchant_name = '') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/correction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description || '',
          correct_category: correct_category,
          amount: parseFloat(amount) || null,
          merchant_name: merchant_name || ''
        })
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error submitting correction:', error);
      throw error;
    }
  }
  
  static async getCategories() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/categories`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      const result = await response.json();
      return result.categories;
    } catch (error) {
      console.error('Error getting categories:', error);
      throw error;
    }
  }
  
  // =====================
  // RECEIPT SCANNING APIs
  // =====================
  
  static async uploadReceipt(imageUri, userId = 'anonymous') {
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: imageUri,
        type: 'image/jpeg',
        name: 'receipt.jpg',
      });
      formData.append('user_id', userId);
      
      const response = await fetch(`${API_BASE_URL}/api/upload-receipt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading receipt:', error);
      throw error;
    }
  }
  
  static async saveExpense(userId, expenseData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/save-expense`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          expense_data: expenseData
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Save failed: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error saving expense:', error);
      throw error;
    }
  }
  
  static async getUserExpenses(userId, options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.limit) params.append('limit', options.limit);
      if (options.start_date) params.append('start_date', options.start_date);
      if (options.end_date) params.append('end_date', options.end_date);
      
      const queryString = params.toString();
      const url = `${API_BASE_URL}/api/expenses/${userId}${queryString ? '?' + queryString : ''}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting user expenses:', error);
      throw error;
    }
  }
  
  static async getExpenseDetails(expenseId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/expense/${expenseId}`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting expense details:', error);
      throw error;
    }
  }
  
  static async updateExpense(expenseId, updateData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/expense/${expenseId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating expense:', error);
      throw error;
    }
  }
  
  static async deleteExpense(expenseId, userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/expense/${expenseId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error deleting expense:', error);
      throw error;
    }
  }
  
  static async getUserSummary(userId, period = 'month') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/user-summary/${userId}?period=${period}`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting user summary:', error);
      throw error;
    }
  }
  
  static async getCategoryStats(userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/categories/${userId}`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting category stats:', error);
      throw error;
    }
  }
  
  // =====================
  // HEALTH CHECK API
  // =====================
  
  static async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error checking health:', error);
      throw error;
    }
  }
}
```

### React Component Example

```javascript
// components/FinzeExpenseManager.js
import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  Alert, 
  StyleSheet, 
  FlatList, 
  Image,
  ScrollView 
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { FinzeAPI } from '../services/FinzeAPI';

const FinzeExpenseManager = () => {
  const [activeTab, setActiveTab] = useState('categorize'); // 'categorize' or 'receipt'
  
  // Categorization state
  const [merchant, setMerchant] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Receipt scanning state
  const [receiptImage, setReceiptImage] = useState(null);
  const [receiptResult, setReceiptResult] = useState(null);
  const [processingReceipt, setProcessingReceipt] = useState(false);
  
  // General state
  const [categories, setCategories] = useState([]);
  const [serverStatus, setServerStatus] = useState(null);
  const [userId] = useState('user_123'); // In real app, get from auth

  useEffect(() => {
    checkServerHealth();
    loadCategories();
    requestCameraPermissions();
  }, []);

  const requestCameraPermissions = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Camera roll permission is required to scan receipts');
    }
  };

  const checkServerHealth = async () => {
    try {
      const health = await FinzeAPI.healthCheck();
      setServerStatus(health);
    } catch (error) {
      setServerStatus({ status: 'error', message: error.message });
    }
  };

  const loadCategories = async () => {
    try {
      const cats = await FinzeAPI.getCategories();
      setCategories(cats);
    } catch (error) {
      console.log('Could not load categories:', error);
    }
  };

  // =====================
  // CATEGORIZATION FUNCTIONS
  // =====================

  const handleCategorize = async () => {
    if (!description.trim()) {
      Alert.alert('Error', 'Please enter a description');
      return;
    }

    setLoading(true);
    try {
      const categorization = await FinzeAPI.categorizeExpense(
        description,
        amount,
        merchant
      );
      setResult(categorization);
    } catch (error) {
      Alert.alert('Error', 'Failed to categorize expense: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCorrection = async (correctCategory) => {
    try {
      await FinzeAPI.submitCorrection(
        description,
        correctCategory,
        amount,
        merchant
      );
      Alert.alert('Success', 'Correction submitted! This will help improve the model.');
    } catch (error) {
      Alert.alert('Error', 'Failed to submit correction: ' + error.message);
    }
  };

  // =====================
  // RECEIPT SCANNING FUNCTIONS
  // =====================

  const pickReceiptImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setReceiptImage(result.assets[0]);
        setReceiptResult(null);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to pick image: ' + error.message);
    }
  };

  const takeReceiptPhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Camera permission is required');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        setReceiptImage(result.assets[0]);
        setReceiptResult(null);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to take photo: ' + error.message);
    }
  };

  const processReceipt = async () => {
    if (!receiptImage) {
      Alert.alert('Error', 'Please select a receipt image first');
      return;
    }

    setProcessingReceipt(true);
    try {
      const result = await FinzeAPI.uploadReceipt(receiptImage.uri, userId);
      
      if (result.status === 'success') {
        setReceiptResult(result.data);
        Alert.alert('Success', 'Receipt processed successfully!');
      } else {
        throw new Error(result.error || 'Processing failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to process receipt: ' + error.message);
    } finally {
      setProcessingReceipt(false);
    }
  };

  const saveReceiptExpense = async () => {
    if (!receiptResult) return;

    try {
      const result = await FinzeAPI.saveExpense(userId, receiptResult);
      Alert.alert('Success', 'Expense saved successfully!');
      // Reset receipt state
      setReceiptImage(null);
      setReceiptResult(null);
    } catch (error) {
      Alert.alert('Error', 'Failed to save expense: ' + error.message);
    }
  };

  // =====================
  // UTILITY FUNCTIONS
  // =====================

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return '#28a745';
    if (confidence > 0.6) return '#ffc107';
    return '#dc3545';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  // =====================
  // RENDER FUNCTIONS
  // =====================

  const renderServerStatus = () => (
    <View style={[styles.statusContainer, { 
      backgroundColor: serverStatus?.status === 'healthy' ? '#d4edda' : '#f8d7da' 
    }]}>
      <Text style={styles.statusText}>
        Server: {serverStatus?.status || 'checking...'}
        {serverStatus?.services && 
          ` | AI: ${serverStatus.services.ai_categorization ? '✓' : '✗'} | Receipts: ${serverStatus.services.receipt_scanning ? '✓' : '✗'}`
        }
      </Text>
    </View>
  );

  const renderCategorizationTab = () => (
    <View style={styles.tabContent}>
      <TextInput
        style={styles.input}
        placeholder="Merchant Name (optional)"
        value={merchant}
        onChangeText={setMerchant}
      />
      
      <TextInput
        style={styles.input}
        placeholder="Description *"
        value={description}
        onChangeText={setDescription}
      />
      
      <TextInput
        style={styles.input}
        placeholder="Amount"
        value={amount}
        onChangeText={setAmount}
        keyboardType="numeric"
      />
      
      <TouchableOpacity 
        style={[styles.button, loading && styles.buttonDisabled]} 
        onPress={handleCategorize}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Categorizing...' : 'Categorize Expense'}
        </Text>
      </TouchableOpacity>
      
      {result && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>AI Prediction:</Text>
          <View style={styles.predictionRow}>
            <Text style={[styles.category, { color: getConfidenceColor(result.confidence) }]}>
              {result.category}
            </Text>
            <Text style={styles.confidence}>
              {(result.confidence * 100).toFixed(1)}%
            </Text>
          </View>
          
          <Text style={styles.suggestionsTitle}>Alternative suggestions:</Text>
          {result.suggested?.slice(1, 3).map((suggestion, index) => (
            <TouchableOpacity 
              key={index}
              style={styles.suggestionRow}
              onPress={() => handleCorrection(suggestion[0])}
            >
              <Text style={styles.suggestion}>
                {suggestion[0]} ({(suggestion[1] * 100).toFixed(1)}%)
              </Text>
            </TouchableOpacity>
          ))}
          
          <Text style={styles.correctionTitle}>Wrong prediction?</Text>
          <FlatList
            data={categories}
            horizontal
            showsHorizontalScrollIndicator={false}
            keyExtractor={(item) => item}
            renderItem={({ item }) => (
              <TouchableOpacity 
                style={styles.categoryChip}
                onPress={() => handleCorrection(item)}
              >
                <Text style={styles.categoryChipText}>{item}</Text>
              </TouchableOpacity>
            )}
          />
        </View>
      )}
    </View>
  );

  const renderReceiptTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.receiptControls}>
        <TouchableOpacity style={styles.receiptButton} onPress={takeReceiptPhoto}>
          <Text style={styles.receiptButtonText}>📷 Take Photo</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.receiptButton} onPress={pickReceiptImage}>
          <Text style={styles.receiptButtonText}>📁 Choose Image</Text>
        </TouchableOpacity>
      </View>

      {receiptImage && (
        <View style={styles.receiptPreview}>
          <Image source={{ uri: receiptImage.uri }} style={styles.receiptImage} />
          
          <TouchableOpacity 
            style={[styles.button, processingReceipt && styles.buttonDisabled]}
            onPress={processReceipt}
            disabled={processingReceipt}
          >
            <Text style={styles.buttonText}>
              {processingReceipt ? 'Processing...' : 'Process Receipt'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {receiptResult && (
        <ScrollView style={styles.receiptResult}>
          <Text style={styles.resultTitle}>Extracted Data:</Text>
          
          <View style={styles.receiptDataRow}>
            <Text style={styles.receiptLabel}>Merchant:</Text>
            <Text style={styles.receiptValue}>{receiptResult.merchant_name}</Text>
          </View>
          
          <View style={styles.receiptDataRow}>
            <Text style={styles.receiptLabel}>Total:</Text>
            <Text style={styles.receiptValue}>{formatCurrency(receiptResult.total_amount)}</Text>
          </View>
          
          <View style={styles.receiptDataRow}>
            <Text style={styles.receiptLabel}>Date:</Text>
            <Text style={styles.receiptValue}>{receiptResult.date}</Text>
          </View>
          
          <View style={styles.receiptDataRow}>
            <Text style={styles.receiptLabel}>Category:</Text>
            <Text style={styles.receiptValue}>{receiptResult.category}</Text>
          </View>

          {receiptResult.items && receiptResult.items.length > 0 && (
            <View style={styles.itemsList}>
              <Text style={styles.itemsTitle}>Items:</Text>
              {receiptResult.items.map((item, index) => (
                <View key={index} style={styles.itemRow}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemPrice}>{formatCurrency(item.total_price)}</Text>
                </View>
              ))}
            </View>
          )}

          <TouchableOpacity 
            style={[styles.button, styles.saveButton]}
            onPress={saveReceiptExpense}
          >
            <Text style={styles.buttonText}>Save Expense</Text>
          </TouchableOpacity>
        </ScrollView>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Finze Expense Manager</Text>
      
      {renderServerStatus()}
      
      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'categorize' && styles.activeTab]}
          onPress={() => setActiveTab('categorize')}
        >
          <Text style={[styles.tabText, activeTab === 'categorize' && styles.activeTabText]}>
            🤖 AI Categorize
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'receipt' && styles.activeTab]}
          onPress={() => setActiveTab('receipt')}
        >
          <Text style={[styles.tabText, activeTab === 'receipt' && styles.activeTabText]}>
            📸 Scan Receipt
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Tab Content */}
      {activeTab === 'categorize' ? renderCategorizationTab() : renderReceiptTab()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
  },
  statusContainer: {
    padding: 10,
    borderRadius: 5,
    marginBottom: 15,
  },
  statusText: {
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '500',
  },
  tabContainer: {
    flexDirection: 'row',
    marginBottom: 20,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  tab: {
    flex: 1,
    padding: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeTabText: {
    color: 'white',
  },
  tabContent: {
    flex: 1,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 12,
    marginBottom: 10,
    borderRadius: 8,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  saveButton: {
    backgroundColor: '#28a745',
    marginTop: 10,
  },
  resultContainer: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  predictionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  category: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  confidence: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  suggestionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 5,
    color: '#666',
  },
  suggestionRow: {
    paddingVertical: 4,
  },
  suggestion: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: 10,
  },
  correctionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 15,
    marginBottom: 8,
    color: '#666',
  },
  categoryChip: {
    backgroundColor: '#e9ecef',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  categoryChipText: {
    fontSize: 12,
    color: '#495057',
    fontWeight: '500',
  },
  // Receipt specific styles
  receiptControls: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  receiptButton: {
    flex: 1,
    backgroundColor: '#28a745',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 5,
  },
  receiptButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  receiptPreview: {
    alignItems: 'center',
    marginBottom: 20,
  },
  receiptImage: {
    width: 200,
    height: 200,
    borderRadius: 8,
    marginBottom: 15,
    resizeMode: 'cover',
  },
  receiptResult: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e9ecef',
    maxHeight: 400,
  },
  receiptDataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  receiptLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
  },
  receiptValue: {
    fontSize: 14,
    color: '#333',
    flex: 1,
    textAlign: 'right',
  },
  itemsList: {
    marginTop: 15,
  },
  itemsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  itemName: {
    fontSize: 12,
    color: '#666',
    flex: 1,
  },
  itemPrice: {
    fontSize: 12,
    color: '#333',
    fontWeight: '500',
  },
});

export default FinzeExpenseManager;
```

### Usage in App.js

```javascript
import React from 'react';
import { SafeAreaView } from 'react-native';
import FinzeExpenseManager from './components/FinzeExpenseManager';

export default function App() {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <FinzeExpenseManager />
    </SafeAreaView>
  );
}
```

### Required Dependencies

```bash
# Install required packages
npm install expo-image-picker

# Or if using yarn
yarn add expo-image-picker
```

### Installation Notes

1. **Update API_BASE_URL**: Replace `YOUR_SERVER_IP` with your actual server IP
2. **For local development**: Use your computer's IP address (find with `ipconfig` on Windows)
3. **For production**: Use your deployed server URL
4. **Camera permissions**: The app will request camera and photo library permissions automatically

### Backend Setup

Make sure your backend is running:

```bash
cd Backend
.\Start_Backend.bat
```

Your backend will be available at `http://localhost:8001` with all endpoints:

#### AI Categorization Endpoints
- `GET /api/health` - System health check
- `GET /api/categories` - Get available categories  
- `POST /api/categorize` - Categorize single expense
- `POST /api/categorize-batch` - Batch categorization
- `POST /api/correction` - Submit corrections

#### Receipt Scanning Endpoints
- `POST /api/upload-receipt` - Upload and process receipt
- `POST /api/save-expense` - Save expense to database
- `GET /api/expenses/<user_id>` - Get user expenses
- `GET /api/expense/<expense_id>` - Get specific expense
- `PUT /api/expense/<expense_id>` - Update expense
- `DELETE /api/expense/<expense_id>` - Delete expense
- `GET /api/user-summary/<user_id>` - Get user analytics
- `GET /api/categories/<user_id>` - Get category statistics

### Example Usage

#### AI Categorization
```javascript
// Simple categorization
const result = await FinzeAPI.categorizeExpense(
  "Morning coffee at Starbucks", 
  5.50,
  "Starbucks"
);

console.log(`Category: ${result.category}, Confidence: ${result.confidence}`);

// Batch processing  
const expenses = [
  {description: "Uber ride home", amount: 25.00, merchant_name: "Uber"},
  {description: "Lunch at McDonald's", amount: 8.50, merchant_name: "McDonald's"}
];
const results = await FinzeAPI.categorizeExpenses(expenses);
```

#### Receipt Scanning
```javascript
// Upload and process receipt
const receiptResult = await FinzeAPI.uploadReceipt(imageUri, 'user123');

if (receiptResult.status === 'success') {
  const expenseData = receiptResult.data;
  
  // Save the extracted expense
  await FinzeAPI.saveExpense('user123', expenseData);
  
  console.log(`Extracted: ${expenseData.merchant_name} - $${expenseData.total_amount}`);
}
```

#### User Expense Management
```javascript
// Get user's expenses
const expenses = await FinzeAPI.getUserExpenses('user123', {
  limit: 50,
  start_date: '2025-01-01',
  end_date: '2025-12-31'
});

// Get user analytics
const summary = await FinzeAPI.getUserSummary('user123', 'month');
console.log(`Total spent this month: $${summary.total_amount}`);

// Get category breakdown
const categoryStats = await FinzeAPI.getCategoryStats('user123');
```

### Configuration

#### Environment Variables (Backend)
```bash
# Optional: For receipt scanning
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For Firebase Firestore
GOOGLE_APPLICATION_CREDENTIALS=path/to/firebase-credentials.json
```

#### API Configuration (Frontend)
```javascript
// Update in services/FinzeAPI.js
const API_BASE_URL = 'http://192.168.1.100:8001'; // Your actual IP

// For production
const API_BASE_URL = 'https://your-domain.com';
```
